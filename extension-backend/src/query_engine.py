from common.aws_utilities import download_file_from_s3
from database.cache import retrieve_session_data
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, get_response_synthesizer
from llama_index.core.tools import QueryPlanTool, QueryEngineTool
from llama_index.agent.openai import OpenAIAgent
import tempfile
import os

class PrevMeetingQueryEngine:
    def __init__(self, session_data):
        self.session_data = session_data

    def get_transcript_path(self):
        self.transcript_path_list = self.session_data["relational_db_obj"].fetch_prev_transcript_path(self.session_data["meeting_name"])

    def handle_files_from_s3(self):
        local_transcript_paths = []

        with tempfile.TemporaryDirectory() as temp_dir:
            for transcript_path in self.transcript_path_list:
                local_file_path = os.path.join(temp_dir, os.path.basename(transcript_path))
                download_file_from_s3(self.session_data["s3_client"], transcript_path, local_file_path)
                local_transcript_paths.append(local_file_path)

        return local_transcript_paths

    def create_tool(self):
        if self.transcript_path_list:
            local_transcript_paths = self.handle_files_from_s3()

            if len(local_transcript_paths) != 0:
                files = SimpleDirectoryReader(input_files=local_transcript_paths).load_data()
                prev_meeting_index = VectorStoreIndex.from_documents(files)
                prev_meeting_engine = prev_meeting_index.as_query_engine(similarity_top_k=3, llm=self.session_data["init_obj"].llm)

                self.prev_meeting_query_tool = QueryEngineTool.from_defaults(
                    query_engine=prev_meeting_engine, 
                    name=self.session_data["meeting_name"],
                    description=(f"Provides transcripts from previous meetings"),
                    )
        else:
            self.prev_meeting_query_tool = None

    def create_query_engine(self):
        self.get_transcript_path()
        self.create_tool()


class CurrMeetingQueryEngine:
    def __init__(self, session_id):
        self.session_data = retrieve_session_data(session_id)

    def get_transcript_path(self):
        self.transcript_path = self.session_data["relational_db_obj"].fetch_curr_transcript_path()

    def handle_files_from_s3(self):
        self.transcript = download_file_from_s3(self.session_data["s3_client"], self.transcript_path)

    def create_tool(self):
        if self.transcript_path:
            self.handle_files_from_s3()
            files = SimpleDirectoryReader(input_files=self.transcript).load_data()
            curr_meeting_index = VectorStoreIndex.from_documents(files)
            curr_meeting_engine = curr_meeting_index.as_query_engine(similarity_top_k=3, llm=self.init_obj.llm)

            self.curr_meeting_query_tool = QueryEngineTool.from_defaults(
                query_engine=curr_meeting_engine, 
                name=self.session_data["meeting_name"],
                description=(f"Provides transcripts from current meeting till this point in time"),
                )
        else:
            self.curr_meeting_query_tool = None

    def create_query_engine(self):
        self.get_transcript_path()
        self.create_tool()


class UserInteraction(CurrMeetingQueryEngine):   
    def __init__(self, session_id):
        super().__init__(session_id)

    def create_plan_tool(self):
        super().create_query_engine()

        response_synthesizer = get_response_synthesizer()
        
        if self.session_data["prev_meeting_obj"].prev_meeting_query_tool and self.curr_meeting_query_tool:
            tools = [self.session_data["prev_meeting_obj"].prev_meeting_query_tool, self.curr_meeting_query_tool]
        elif self.session_data["prev_meeting_obj"].prev_meeting_query_tool:
            tools = [self.session_data["prev_meeting_obj"].prev_meeting_query_tool]
        elif self.curr_meeting_query_tool:
            tools = [self.curr_meeting_query_tool]
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
            llm=self.session_data["init_obj"].llm,
            verbose=True,
        )

    def get_response(self, user_query):
        self.agent.query(user_query)
        return str(self.response)        

    def query_response_pipeline(self, user_query):
        self.create_plan_tool()
        if self.query_plan_tool:
            self.create_agent()
            return self.get_response(user_query)
        else:
            return None


def setup_prev_meeting_query_engine(session_data):
    prev_meeting_query_engine = PrevMeetingQueryEngine(session_data)
    prev_meeting_query_engine.create_query_engine()
    return prev_meeting_query_engine