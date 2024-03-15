from database.vector_store import VectorStore

import os
from flask import current_app
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
from pinecone import Pinecone
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.llms.openai import OpenAI

class Initialisation:
    def __init__(self):
        load_dotenv()

    def initialise_vector_dbs(self):
        self.db_audio = Pinecone(api_key=os.getenv("DB_API_AUDIO"))
        self.db_transcript = Pinecone(api_key=os.getenv("DB_API_TRANSCRIPT"))

    def initialise_models(self):
        self.asr_model = WhisperModel("base")
        self.diarization_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.0", use_auth_token=os.getenv("HF_API"))
        self.embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.llm = OpenAI(openai_api_key=os.getenv("OPENAI_API"))

def initialise_objects():
    init_obj = Initialisation()
    init_obj.initialise_vector_dbs()
    init_obj.initialise_models()
    
    vector_store_obj = VectorStore()

    current_app.config["init_obj"] = init_obj
    current_app.config["vector_store_obj"] = vector_store_obj

    vector_store_obj.create_index()
    

    
