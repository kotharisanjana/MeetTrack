from common.aws_utilities import download_file_from_s3
from database.relational_db import fetch_prev_transcript_path
from src.guardrails.user_interaction_gr import UserInteractionGR
import common.globals as global_vars
from __init__ import llm, logger

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, get_response_synthesizer
from llama_index.core.tools import QueryPlanTool, QueryEngineTool
from llama_index.agent.openai import OpenAIAgent
import os

user_interaction_gr_obj = UserInteractionGR()

class PrevMeetingQueryEngine:
    def __init__(self, meeting_name, meeting_id):
        self.meeting_name = meeting_name
        self.meeting_id = meeting_id

    def get_transcript_path(self):
        # if recurring meeting then fetch S3 paths of all previous transcripts
        self.transcript_path_list = fetch_prev_transcript_path(self.meeting_name, self.meeting_id)

    def handle_files_from_s3(self):
        local_transcript_paths = []

        # download all previous transcripts from S3
        for transcript_path in self.transcript_path_list:
            local_filepath = os.path.join(global_vars.DOWNLOAD_DIR, f"{self.meeting_id}/prev", transcript_path.split("/")[-1])
            download_file_from_s3(transcript_path, local_filepath)
            local_transcript_paths.append(local_filepath)

        return local_transcript_paths

    def create_tool(self):
        if self.transcript_path_list:
            local_transcript_paths = self.handle_files_from_s3()

            if len(local_transcript_paths) != 0:
                # create query engine tool for previous meetings from the transcripts
                files = SimpleDirectoryReader(input_files=local_transcript_paths).load_data()
                prev_meeting_index = VectorStoreIndex.from_documents(files)

                prev_meeting_engine = prev_meeting_index.as_query_engine(similarity_top_k=3, llm=llm)

                self.prev_meeting_query_tool = QueryEngineTool.from_defaults(
                    query_engine=prev_meeting_engine, 
                    name=self.meeting_name,
                    description=(f"Provides transcripts from previous meetings"),
                    )
        else:
            # if previous transcripts are not available, set tool to None
            self.prev_meeting_query_tool = None

    def get_tool(self):
        return self.prev_meeting_query_tool

    def create_query_engine(self):
        self.get_transcript_path()
        self.create_tool()
        return self.get_tool()


class CurrMeetingQueryEngine:
    def __init__(self, meeting_name, local_transcript_path):
        self.meeting_name = meeting_name
        self.local_transcript_path = local_transcript_path

    def create_tool(self):
        files = SimpleDirectoryReader(input_files=[self.local_transcript_path]).load_data()
        curr_meeting_index = VectorStoreIndex.from_documents(files)

        # create query engine tool for current meeting from the transcript
        curr_meeting_engine = curr_meeting_index.as_query_engine(similarity_top_k=3, llm=llm)

        self.curr_meeting_tool = QueryEngineTool.from_defaults(
            query_engine=curr_meeting_engine, 
            name=self.meeting_name,
            description=(f"Provides transcripts from current meeting till this point in time"),
            )

    def create_query_engine(self):
        self.create_tool()


class UserInteraction(CurrMeetingQueryEngine):   
    def __init__(self, meeting_name, local_transcript_path):
        super().__init__(meeting_name, local_transcript_path)

    def create_plan_tool(self, prev_meeting_tool):
        # create query engine tool for current meeting transcript
        super().create_query_engine()

        response_synthesizer = get_response_synthesizer()
        
        # define list of tools based on previous and current meeting tools
        if prev_meeting_tool and self.curr_meeting_tool:
            tools = [prev_meeting_tool, self.curr_meeting_tool]
        elif prev_meeting_tool:
            tools = [self.prev_meeting_tool]
        elif self.curr_meeting_tool:
            tools = [self.curr_meeting_tool]
        else:
            tools = []

        if len(tools) != 0:
            # create query plan tool if tools exist
            self.query_plan_tool = QueryPlanTool.from_defaults(
                query_engine_tools=tools,
                response_synthesizer=response_synthesizer,
                )
        else:
            # if no tools exist, set query plan tool to None
            self.query_plan_tool = None
        
    def create_agent(self):
        # create OpenAI agent with query plan tool to answer user queries
        self.agent = OpenAIAgent.from_tools(
            [self.query_plan_tool],
            max_function_calls=1,
            llm=llm,
            verbose=True,
        )

    def get_response(self, user_query):
        user_query = "Answer user question based on the meeting transcript. Give a brief and accurate answer. " + user_query
        response = self.agent.query(user_query)
        return str(response)        

    def query_response_pipeline(self, prev_meeting_tool, user_query):
        self.create_plan_tool(prev_meeting_tool)
        if self.query_plan_tool:
            self.create_agent()

            agent_resp = self.get_response(user_query)

            if "json" in agent_resp:
                logger.error("Agent did not return a valid response.") 
                return None
                           
            outcome = user_interaction_gr_obj.validate(agent_resp)
            if outcome:
                # if response passes guardrails validation, break out of the loop and return response
                if outcome.reask is None:
                    logger.info("User query response completed and validated.")
                    return agent_resp
            
        logger.error("Error in getting a response for user query.")
        return None