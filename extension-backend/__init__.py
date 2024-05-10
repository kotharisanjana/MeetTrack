import common.globals as global_vars

import os
import logging
import psycopg2
from dotenv import load_dotenv
import boto3
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
from qdrant_client import QdrantClient
from llama_index.llms.openai import OpenAI as LlamaOpenAI
from langchain_openai import ChatOpenAI as LangChainChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import openai
from sentence_transformers import SentenceTransformer
from redis import Redis


# create logger instance
logging.basicConfig(filename=global_vars.LOGGING_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('my_application_logger')

# load .env file
load_dotenv()

# set up OpenAI API key
openai.api_key = os.getenv("OPENAI_API")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API")
os.environ['GOOGLE_API_KEY'] = os.getenv("GOOGLE_API_KEY")

# set up Redis client
redis_client = Redis(host=os.getenv("EC2"), port=6379, db=0)


# set up Postgres connection
try:
    conn = psycopg2.connect(dbname=os.getenv("RELATIONAL_DB_NAME"), 
                        user=os.getenv("RELATIONAL_DB_USERNAME"), 
                        password=os.getenv("RELATIONAL_DB_PASSWORD"), 
                        host=os.getenv("RELATIONAL_DB_HOST"), 
                        port=os.getenv("RELATIONAL_DB_PORT"), 
                        )
    conn_cursor = conn.cursor()
    logger.info("Postgres connection established successfully.")
except psycopg2.Error as e:
    logger.error(f"Postgres connection failed: {e}")


# initialize qdrant client
try :
    vector_db_client = QdrantClient(url=os.getenv("VECTOR_DB_URL"), 
                                    api_key=os.getenv("VECTOR_DB_API")
                                    )
    logger.info("Qdrant client initialized successfully.")
except Exception as e:
    logger.error(f"Qdrant client initialization failed: {e}")


# initialize models
asr_model = WhisperModel("tiny", compute_type="int8")
logger.info("ASR model initialized successfully.")

diarization_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.0", 
                                                use_auth_token=os.getenv("HF_API")
                                                )
logger.info("Diarization pipeline initialized successfully.")

llm = LlamaOpenAI(model="gpt-3.5-turbo", 
             openai_api_key=os.getenv("OPENAI_API"),
             temperature=0,
             )
logger.info("Llama OpenAI model initialized successfully.")

llm_chat = LangChainChatOpenAI(model_name="gpt-3.5-turbo",
                      openai_api_key=os.getenv("OPENAI_API"),
                      temperature=0,
                      )
logger.info("LangChain OpenAI model initialized successfully.")

llm_vision = ChatGoogleGenerativeAI(model="gemini-pro-vision")
logger.info("LangChain Google Generative AI model initialized successfully.")

embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
logger.info("Sentence Transformer model initialized successfully.")

# initialize S3 client
try:
    s3_client = boto3.client("s3", 
                             aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                             aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
                             )
    logger.info("S3 client initialized successfully.")
except Exception as e:
    logger.error(f"S3 client initialization failed: {e}")

    