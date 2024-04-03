from __init__ import vector_db_client
import numpy as np
from qdrant_client.http import models

def get_actual_speaker(speaker_id):
    identified_speaker_record = vector_db_client.retrieve(
        collection_name="identified_speaker_embeddings",
        ids=[speaker_id],
        with_vectors=True
    )
    identified_speaker_vector = identified_speaker_record[0].vector

    speaker_match = vector_db_client.search(
        collection_name="actual_speaker_embeddings", 
        query_vector=identified_speaker_vector, 
        limit=1
    )

    actual_speaker = speaker_match[0].id
    
    return actual_speaker

def store_speaker_embedding(embeddings):
    for i, emb in enumerate(embeddings):
        if np.any(emb):
            vector_db_client.upsert(
                collection_name="identified-speaker-embeddings",
                wait=True,
                points=[
                    models.PointStruct(id=i, payload={"speaker": str(i)}, vector=emb.tolist())
                ]
            )    
        
def store_description_embedding(i, meeting_id, image_url, embedding):
    vector_db_client.upsert(
        collection_name="image-description-embeddings",
        wait=True,
        points=[
            models.PointStruct(id=i, 
                        payload={"meeting_id": meeting_id, "image_url": image_url}, 
                        vector=embedding.tolist())
        ]
    )

def get_relevant_images(meeting_id, summary_embedding):
    res = vector_db_client.search(
        collection_name="image-description-embeddings",
        query_vector=summary_embedding.tolist(),
        top=3,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="meeting_id",
                    range=models.MatchValue(value=meeting_id)
                )
            ]
        ),
    )
    image_links = [match.payload["image_url"] for match in res]
    return image_links