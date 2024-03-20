import numpy as np
from qdrant_client.http.models import PointStruct

class VectorDb:
    def __init__(self, session_data):
        self.init_obj = session_data["init_obj"]

    def get_actual_speaker(self, speaker_id):
        identified_speaker_record = self.init_obj.vector_db_client.retrieve(
            collection_name="identified_speaker_embeddings",
            ids=[speaker_id],
            with_vectors=True
        )
        identified_speaker_vector = identified_speaker_record[0].vector

        speaker_match = self.init_obj.vector_db_client.search(
            collection_name="actual_speaker_embeddings", 
            query_vector=identified_speaker_vector, 
            limit=1
        )

        actual_speaker = speaker_match[0].id
        
        return actual_speaker

    def insert_identified_speaker_embedding(self, embeddings):
        for i, emb in enumerate(embeddings):
            if np.any(emb):
                self.init_obj.vector_db_client.upsert(
                    collection_name="identified_speaker_embeddings",
                    wait=True,
                    points=[
                        PointStruct(id=str(i), vector=emb.tolist())
                    ]
                )

    def insert_actual_speaker_embedding(self, speaker_name, voice_embedding):
        self.init_obj.vector_db_client.upsert(
            collection_name="actual_speaker_embeddings",
            wait=True,
            points=[
                PointStruct(id=speaker_name, vector=voice_embedding[0].tolist())
            ]
        )