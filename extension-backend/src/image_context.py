from moviepy.editor import VideoFileClip
import numpy as np
from PIL import Image
import os
import io
import boto3
from tqdm.auto import tqdm
import pandas as pd
from datetime import datetime
import openai
from common.aws_utilities import download_file, upload_frame_to_s3
import csv
import pinecone
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer


path = "s3_video_path"
video_local_path = download_file(path)
bucket_name = ""
object_key=""
s3 = boto3.session("s3")

def capture_screenshots(interval=20):
    """
    Captures screenshots from a video file at specified intervals.

    video_path: Path to the video file.
    interval: Interval in seconds between each screenshot.
    return: List of images.
    """
    clip = VideoFileClip(video_local_path)
    duration = clip.duration
    screenshots = []

    for i in np.arange(0, duration, interval):
        video_timestamp = str(datetime.utcfromtimestamp(i).strftime('%H-%M-%S'))
        frame = clip.get_frame(i)
        screenshots.append(frame)
        object_name = f"screenshots/screenshot_{video_timestamp}.png"
        upload_frame_to_s3(frame, bucket_name, object_name)
   


def initialize_openai_client():
    openai.api_key = '*'
    return openai

def generate_captions(image_urls):
    client = initialize_openai_client()
    # upload_file(bucket_name,object_key,screenshots) --- upload screenshots on s3
    capture_screenshots()
    descriptions = {}
    
    for url in image_urls:
        try:
            response = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What’s in this image? describe it in 3 lines"},
                            {"type": "image_url", "image_url": {"url": url}},
                        ],
                    }
                ],
                max_tokens=300,
            )

            content = response.choices
            description = content[0].message.content
            descriptions[url] = description.strip()
            descriptions.to_csv("localpath")
            # s3.upload_file(bucket_name,object_key,local_path)
        except Exception as e:
            print(f"Error processing {url}: {e}")
            descriptions[url] = "Error retrieving description"

    return descriptions

def create_embedding(text):
  model = SentenceTransformer("avsolatorio/GIST-Embedding-v0")
  embedding = model.encode(text)
  return embedding


def generate_embeddings():
    # image_urls = download_file(bucket_name,image_path)- download images from s3 -- see if gpt4 can access s3 urls (get_object)
    descriptions_dict = generate_captions(image_urls)
    descriptions_df = pd.DataFrame(list(descriptions_dict.items()), columns=["image_url", "description"])
    descriptions_df["embeddings"] = None 
    for index,row in tqdm(descriptions_df.iterrows(),total = descriptions_df.shape[0]):
        embedding = create_embedding(row['description'])
        descriptions_df.at[index, 'embeddings'] = embedding
    descriptions_df.to_csv("local_path")
    # s3.upload_file(bucket_name,object_key,local_path)

def init_pinecone(api_key, index_name):
    """
    Initialize Pinecone, create an index if it doesn't exist, and connect to it.

    Parameters:
    - api_key (str): Pinecone API key.
    - index_name (str): The name of the Pinecone index to create or connect to.

    Returns:
    - A Pinecone Index object connected to the specified index.
    """
    pc = Pinecone(api_key=api_key)

    try:
        pc.create_index(
            name=index_name,
            dimension=768,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-west-2")
        )
        print(f"Index '{index_name}' created.")
    except Exception as e:
        print(f"Could not create index '{index_name}'. It might already exist. Error: {e}")

    # Connect to the index
    index = pc.Index(name=index_name)
    print(f"Connected to index '{index_name}'.")

    return index

def upsert_records(df, index):
    records_to_upsert = []
    for idx, row in tqdm(df.iterrows(), total=df.shape[0], desc="Upserting records"):
        unique_id = str(idx)
        vector_entry = {
            "id": unique_id,
            "values": row['embeddings'],
            "metadata": {col: row[col] for col in df.columns if col not in ['embeddings']}
        }
        records_to_upsert.append(vector_entry)

    index.upsert(vectors=records_to_upsert)

def create_pinecone_index():
    api_key = ""
    index_name = "textimagecontext"
    index = init_pinecone(api_key, index_name)
    generate_embeddings()
    # df_file = s3.download_file(bucket_name,object_key,local_path)
    df = pd.read_csv("local_path")
    upsert_records(df, index)

# hardcode index name once its created
def get_images_from_context(summary):
   query_embedding = create_embedding(summary)
   res = index.query(
    vector=query_embedding.tolist(),
    top_k=2,
    include_metadata=True
)
   image_links = [match['metadata']['Image_link'] for match in res['matches']]
   return image_links 