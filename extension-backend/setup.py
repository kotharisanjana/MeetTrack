from embeddings import VoiceEmbeddings
from vector_store import VectorStore

import os
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
from pinecone import Pinecone
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.llms.openai import OpenAI

class Setup:
    MEETING_NAME = ""
    MEETING_DATE = ""
    OUTPUT_TRANSCRIPT_FILE = ""
    # specify path where actual speaker voice files are stored
    ACTUAL_AUDIO_PATH = ""

    def __init__(self):
        load_dotenv()

    def initialise_vector_dbs(self):
        self.db_audio = Pinecone(api_key=os.getenv("DB_API_AUDIO"))
        self.db_transcript = Pinecone(api_key=os.getenv("DB_API_TRANSCRIPT"))

    def initialise_models(self):
        self.asr_model = WhisperModel("base")
        self.diarization_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.0", use_auth_token=os.getenv("HF_TOKEN"))
        self.embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.llm = OpenAI(openai_api_key=os.getenv("OPENAI_API"))

# Initialise objects  
setup_obj = Setup()
setup_obj.initialise_vector_dbs()
setup_obj.initialise_models()

# set up vector database indices
vector_db_obj = VectorStore()
vector_db_obj.create_index()

# store actual voice embeddings
VoiceEmbeddings().actual_audio_embedding_pipeline()
