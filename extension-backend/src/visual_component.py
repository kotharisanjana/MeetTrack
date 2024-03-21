from __init__ import llm_vision
from tqdm.auto import tqdm
import pandas as pd
from sentence_transformers import SentenceTransformer

// fix!!
class VisualComponent:
    def generate_captions(image_urls):
        descriptions = {}
        for url in image_urls:
            try:
                response = llm_vision.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "What's in this image? Describe it in 3 lines"},
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
                # insert path in postgres
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