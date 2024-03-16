from database.vector_db import VectorDb
import os
from flask import current_app
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
from qdrant_client import QdrantClient
from langchain.llms.openai import OpenAI

class Initialisation:
    def __init__(self):
        load_dotenv()

    def initialise_vector_db(self):
        self.vector_db_client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API"))

    def initialise_models(self):
        self.asr_model = WhisperModel("base")
        self.diarization_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.0", use_auth_token=os.getenv("HF_API"))
        self.llm = OpenAI(temperature=0, model="gpt-4", openai_api_key=os.getenv("OPENAI_API"))

def initialise_objects():
    init_obj = Initialisation()
    init_obj.initialise_vector_db()
    init_obj.initialise_models()
    
    vector_db_obj = VectorDb()

    current_app.config["init_obj"] = init_obj
    current_app.config["vector_db_obj"] = vector_db_obj    

    
