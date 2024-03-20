import os
import psycopg2
from dotenv import load_dotenv
import boto3
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
from qdrant_client import QdrantClient
from langchain.llms.openai import OpenAI

class Initialisation:
    def __init__(self):
        load_dotenv()

    def initialise_relational_db(self):
        conn = psycopg2.connect(
            dbname=os.getenv("RELATIONAL_DB_NAME"), 
            user=os.getenv("RELATIONAL_DB_USERNAME"), 
            password=os.getenv("RELATIONAL_DB_PASSWORD"), 
            host=os.getenv("RELATIONAL_DB_HOST"), 
            port=os.getenv("RELATIONAL_DB_PORT"), 
        )
        self.conn_cursor = conn.cursor()

    def initialise_vector_db(self):
        self.vector_db_client = QdrantClient(url=os.getenv("VECTOR_DB_URL"), api_key=os.getenv("VECTOR_DB_API"))

    def initialise_models(self):
        self.asr_model = WhisperModel("base")
        self.diarization_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.0", use_auth_token=os.getenv("HF_API"))
        self.llm = OpenAI(temperature=0, model="gpt-4", openai_api_key=os.getenv("OPENAI_API"))

    def initialise_boto3_client(self):
        self.s3_client = boto3.client("s3")

def initialise(app):
    init_obj = Initialisation()
    init_obj.initialise_relational_db()
    init_obj.initialise_vector_db()
    init_obj.initialise_models()
    init_obj.initialise_boto3_client()
    
    app.config["init_obj"] = init_obj
    
