from common.aws_utilities import download_textfile_from_s3, download_file_from_s3
from database.relational_db import fetch_prev_transcript_path, fetch_curr_transcript_path
from common.globals import DOWNLOAD_DIR
from __init__ import llm
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, get_response_synthesizer
from llama_index.core.tools import QueryPlanTool, QueryEngineTool
from llama_index.agent.openai import OpenAIAgent
import os

class PrevMeetingQueryEngine:
    def __init__(self, meeting_name, meeting_id):
        self.meeting_name = meeting_name
        self.meeting_id = meeting_id

    def get_transcript_path(self):
        self.transcript_path_list = fetch_prev_transcript_path(self.meeting_name, self.meeting_id)

    def handle_files_from_s3(self):
        local_transcript_paths = []
        for transcript_path in self.transcript_path_list:
            local_file_path = os.path.join(DOWNLOAD_DIR, transcript_path.split("/")[-1])
            download_file_from_s3(transcript_path, local_file_path)
            local_transcript_paths.append(local_file_path)
        return local_transcript_paths

    def create_tool(self):
        if self.transcript_path_list:
            local_transcript_paths = self.handle_files_from_s3()

            if len(local_transcript_paths) != 0:
                files = SimpleDirectoryReader(input_files=local_transcript_paths).load_data()
                prev_meeting_index = VectorStoreIndex.from_documents(files)
                prev_meeting_engine = prev_meeting_index.as_query_engine(similarity_top_k=3, llm=llm)

                self.prev_meeting_query_tool = QueryEngineTool.from_defaults(
                    query_engine=prev_meeting_engine, 
                    name=self.meeting_name,
                    description=(f"Provides transcripts from previous meetings"),
                    )
        else:
            self.prev_meeting_query_tool = None

    def get_tool(self):
        return self.prev_meeting_query_tool

    def create_query_engine(self):
        self.get_transcript_path()
        self.create_tool()
        return self.get_tool()


class CurrMeetingQueryEngine:
    def __init__(self, meeting_id, meeting_name):
        self.meeting_id = meeting_id
        self.meeting_name = meeting_name

    def get_transcript_path(self):
        self.transcript_path = fetch_curr_transcript_path(self.meeting_id)

    def handle_files_from_s3(self):
        self.local_file_path = os.path.join(DOWNLOAD_DIR, self.transcript_path.split("/")[-1])

    def create_tool(self):
        self.handle_files_from_s3()
        files = SimpleDirectoryReader(input_files=[self.local_file_path]).load_data()
        curr_meeting_index = VectorStoreIndex.from_documents(files)
        curr_meeting_engine = curr_meeting_index.as_query_engine(similarity_top_k=3, llm=llm)

        self.curr_meeting_tool = QueryEngineTool.from_defaults(
            query_engine=curr_meeting_engine, 
            name=self.meeting_name,
            description=(f"Provides transcripts from current meeting till this point in time"),
            )

    def create_query_engine(self):
        self.get_transcript_path()
        self.create_tool()


class UserInteraction(CurrMeetingQueryEngine):   
    def __init__(self, meeting_id, meeting_name):
        super().__init__(meeting_id, meeting_name)

    def create_plan_tool(self, prev_meeting_tool):
        super().create_query_engine()

        response_synthesizer = get_response_synthesizer()
        
        if prev_meeting_tool and self.curr_meeting_tool:
            tools = [prev_meeting_tool, self.curr_meeting_tool]
        elif prev_meeting_tool:
            tools = [self.prev_meeting_tool]
        elif self.curr_meeting_tool:
            tools = [self.curr_meeting_tool]
        else:
            tools = []

        if len(tools) != 0:
            self.query_plan_tool = QueryPlanTool.from_defaults(
                query_engine_tools=tools,
                response_synthesizer=response_synthesizer,
                )
        else:
            self.query_plan_tool = None
        
    def create_agent(self):
        self.agent = OpenAIAgent.from_tools(
            [self.query_plan_tool],
            max_function_calls=2,
            llm=llm,
            verbose=True,
        )

    def get_response(self, user_query):
        response = self.agent.query(user_query)
        return str(response)        

    def query_response_pipeline(self, prev_meeting_tool, user_query):
        self.create_plan_tool(prev_meeting_tool)
        if self.query_plan_tool:
            self.create_agent()
            return self.get_response(user_query)
        else:
            return None


def setup_prev_meeting_query_engine(meeting_name, meeting_id):
    prev_meeting_query_engine = PrevMeetingQueryEngine(meeting_name, meeting_id)
    return prev_meeting_query_engine.create_query_engine()