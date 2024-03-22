import os
import psycopg2
from dotenv import load_dotenv
import boto3
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
from qdrant_client import QdrantClient
from langchain.llms.openai import OpenAI, OpenAIChat

load_dotenv()

conn = psycopg2.connect(dbname=os.getenv("RELATIONAL_DB_NAME"), 
                        user=os.getenv("RELATIONAL_DB_USERNAME"), 
                        password=os.getenv("RELATIONAL_DB_PASSWORD"), 
                        host=os.getenv("RELATIONAL_DB_HOST"), 
                        port=os.getenv("RELATIONAL_DB_PORT"), 
                        )
conn_cursor = conn.cursor()

vector_db_client = QdrantClient(url=os.getenv("VECTOR_DB_URL"), 
                                api_key=os.getenv("VECTOR_DB_API")
                                )

asr_model = WhisperModel("base")

diarization_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.0", 
                                                use_auth_token=os.getenv("HF_API"))

llm = OpenAI(model="gpt-4", 
             openai_api_key=os.getenv("OPENAI_API"),
             temperature=0,
             )

llm_chat = OpenAIChat(model="gpt-3.5-turbo",
                      openai_api_key=os.getenv("OPENAI_API"),
                      temperature=0
                      )

llm_vision = OpenAI(model="gpt-4-vision-preview", 
                    openai_api_key=os.getenv("OPENAI_API")
                    )

s3_client = boto3.client("s3", 
                         aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                         aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
                         )
    
