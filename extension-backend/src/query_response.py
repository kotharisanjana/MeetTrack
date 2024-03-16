from database.storage import *
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, get_response_synthesizer
from llama_index.core.tools import QueryPlanTool, QueryEngineTool
from llama_index.agent.openai import OpenAIAgent
from flask import current_app

class UserInteraction:
    def __init__(self):
        self.init_obj = current_app.config["init_obj"]
        self.meeting_name = self.init_obj.MEETING_NAME

    def get_prev_meeting_transcripts(self):
        self.prev_meetings = []
        if is_recurring_meeting(self.meeting_name):
            self.prev_meetings = retrieve_prev_meeting_transcripts(self.meeting_name)

    def create_tool_prev_meetings(self):
        if len(self.prev_meetings) > 0:
            files = SimpleDirectoryReader(input_files=self.prev_meetings).load_data()
            prev_meetings_index = VectorStoreIndex.from_documents(files)
            prev_meetings_engine = prev_meetings_index.as_query_engine(similarity_top_k=3, llm=self.init_obj.llm)

            self.prev_meetings_query_tool = QueryEngineTool.from_defaults(
                query_engine=prev_meetings_engine, 
                name=self.meeting_name,
                description=(f"Provides transcripts from previous meetings of {self.meeting_name}"),
                )
        else:
            self.prev_meetings_query_tool = None
    
    def create_tool_curr_meeting(self):
        curr_meeting = retrieve_curr_meeting_transcripts(self.meeting_name)

        files = SimpleDirectoryReader(input_files=curr_meeting).load_data()
        curr_meeting_index = VectorStoreIndex.from_documents(files)
        curr_meeting_engine = curr_meeting_index.as_query_engine(similarity_top_k=3, llm=self.init_obj.llm)

        self.curr_meeting_query_tool = QueryEngineTool.from_defaults(
            query_engine=curr_meeting_engine, 
            name=self.meeting_name,
            description=(f"Provides transcripts from current meeting till this point of {self.meeting_name}"),
            )
        
    def create_plan_tool(self):
        response_synthesizer = get_response_synthesizer()
        
        if self.prev_meetings_query_tool:
            tools = [self.prev_meetings_query_tool, self.curr_meeting_query_tool]
        else:
            tools = [self.curr_meeting_query_tool]

        self.query_plan_tool = QueryPlanTool.from_defaults(
            query_engine_tools=tools,
            response_synthesizer=response_synthesizer,
            )
        
    def create_agent(self):
        self.agent = OpenAIAgent.from_tools(
            [self.query_plan_tool],
            max_function_calls=2,
            llm=self.init_obj.llm,
            verbose=True,
            )

    def get_response(self, user_query):
        self.agent.query(user_query)
        return str(self.response)        

    def query_response_pipeline(self, user_query):
        self.create_tool_curr_meeting()
        self.create_plan_tool()
        self.create_agent()
        return self.get_response(user_query)
