from __init__ import vector_db_client
import numpy as np
from qdrant_client.http.models import PointStruct

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

def insert_identified_speaker_embedding(embeddings):
    for i, emb in enumerate(embeddings):
        if np.any(emb):
            vector_db_client.upsert(
                collection_name="identified-speaker-embeddings",
                wait=True,
                points=[
                    PointStruct(id=i, payload={"speaker": str(i)}, vector=emb.tolist())
                ]
            )

def insert_actual_speaker_embedding(speaker_name, voice_embedding):
    vector_db_client.upsert(
        collection_name="actual-speaker-embeddings",
        wait=True,
        points=[
            PointStruct(id=speaker_name, payload={"speaker": speaker_name}, vector=voice_embedding[0].tolist())
        ]
    )