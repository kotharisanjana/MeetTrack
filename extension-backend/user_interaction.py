from setup import setup_obj, vector_db_obj

from collections import defaultdict
from langchain.prompts import PromptTemplate

class UserInteraction:
    def __init__(self, query):
        self.query = query
    
    def get_query_embedding(self, query):
        self.query_embedding = setup_obj.embeddings_model.embed_query(query)
        self.segments = vector_db_obj.get_nearest_segments(self.query_embedding)

    def generate_responses(self):
        self.response = defaultdict(str)

        for segment in self.segments:
            text = segment["metadata"]["segment_text"]
            meeting_date = segment["metadata"]["meeting_date"]

            prompt = PromptTemplate(
                template=""""You are an expert at scanning text and answering questions based on that. Answer user question based on what has been discussed in the meeting so far. 
                question: {question}. 
                meeting transcript segment: {meeting_segment}""",
                input_variables=["question", "meeting_segment"]
            )

            prompt_formatted_str = prompt.format(
                question=self.query,
                meeting_segment=text)

            llm_response = setup_obj.llm.predict(prompt_formatted_str)

            self.response[meeting_date] = llm_response
        
    def format_responses(self):
        for date, segment in self.response.items():
            if date != "meeting_date":
                segment = "Previously discussed on " + date + ": " + segment
            else:
                segment = "From today's meeting: " + segment
        
    def get_response(self):
        return self.response

    def query_response_pipeline(self):
        self.get_query_embedding(self.query)
        self.generate_responses()
        self.format_responses()
        return self.get_response()
