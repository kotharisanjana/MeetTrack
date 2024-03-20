from database.redis import retrieve_session_data
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, get_response_synthesizer
from llama_index.core.tools import QueryPlanTool, QueryEngineTool
from llama_index.agent.openai import OpenAIAgent

class PrevMeetingQueryEngine:
    def __init__(self, session_data):
        self.session_data = session_data

    def get_transcript_prev_meeting(self):
        self.prev_meeting_transcript = self.session_data["relational_db_obj"].get_prev_meeting_transcript(self.session_data["meeting_name"])

    def create_tool_prev_meeting(self):
        if self.prev_meeting_transcript:
            files = SimpleDirectoryReader(input_files=self.prev_meeting_transcript).load_data()
            prev_meeting_index = VectorStoreIndex.from_documents(files)
            prev_meeting_engine = prev_meeting_index.as_query_engine(similarity_top_k=3, llm=self.session_data["init_obj"].llm)

            self.prev_meeting_query_tool = QueryEngineTool.from_defaults(
                query_engine=prev_meeting_engine, 
                name=self.session_data["meeting_name"],
                description=(f"Provides transcripts from previous meetings"),
                )
        else:
            self.prev_meeting_query_tool = None

    def prev_meeting_query_engine(self):
        self.get_transcript_prev_meeting()
        self.create_tool_prev_meeting()


class CurrMeetingQueryEngine:
    def __init__(self, session_id):
        self.session_data = retrieve_session_data(session_id)

    def get_transcript_curr_meeting(self):
        self.curr_meeting_transcript = self.session_data["relational_db_obj"].get_curr_meeting_transcript()

    def create_tool_curr_meeting(self):
        if self.curr_meeting_transcript:
            files = SimpleDirectoryReader(input_files=self.curr_meeting_transcript).load_data()
            curr_meeting_index = VectorStoreIndex.from_documents(files)
            curr_meeting_engine = curr_meeting_index.as_query_engine(similarity_top_k=3, llm=self.init_obj.llm)

            self.curr_meeting_query_tool = QueryEngineTool.from_defaults(
                query_engine=curr_meeting_engine, 
                name=self.session_data["meeting_name"],
                description=(f"Provides transcripts from current meeting till this point in time"),
                )
        else:
            self.curr_meeting_query_tool = None

    def curr_meeting_query_engine(self):
        self.get_transcript_curr_meeting()
        self.create_tool_curr_meeting()


class UserInteraction(CurrMeetingQueryEngine):   
    def __init__(self, session_id):
        super().__init__(session_id)

    def create_plan_tool(self):
        super().curr_meeting_query_engine()

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
    prev_meeting_query_engine.prev_meeting_query_engine()
    return prev_meeting_query_engine