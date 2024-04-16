from __init__ import vector_db_client, logger

import numpy as np
from qdrant_client.http import models

def get_actual_speaker(speaker_id):
    """
    Get the actual speaker from the speaker ID.
    
    :param speaker_id: Speaker ID
    :return: Actual speaker name
    """
    try:
        # retrieve the identified speaker embedding
        identified_speaker_record = vector_db_client.retrieve(
            collection_name="identified-speaker-embeddings",
            ids=[speaker_id],
            with_vectors=True
        )
        identified_speaker_vector = identified_speaker_record[0].vector

        # search for the actual speaker embedding closest to the identified speaker embedding
        speaker_match = vector_db_client.search(
            collection_name="actual-speaker-embeddings", 
            query_vector=identified_speaker_vector, 
            limit=1
        )
        actual_speaker = speaker_match[0].payload["speaker"]   
        return actual_speaker   
    except Exception as e:
        logger.error(f"Error retrieving actual speaker: {e}")
        return None


def store_speaker_embedding(embeddings):
    """
    Store speaker embeddings in the vector database.
    
    :param embeddings: Speaker embeddings
    """
    for i, emb in enumerate(embeddings):
        if np.any(emb):
            try:
                vector_db_client.upsert(
                    collection_name="identified-speaker-embeddings",
                    wait=True,
                    points=[
                        models.PointStruct(id=i, payload={"speaker": str(i)}, vector=emb.tolist())
                    ]
                )    
                logger.info(f"Speaker embedding {i} stored successfully")
            except Exception as e:
                logger.error(f"Error storing speaker embedding {i}: {e}")

        
def store_description_embedding(i, meeting_id, image_url, embedding):
    """
    Store image description embeddings in the vector database.
    
    :param i: Index of the image
    :param meeting_id: ID of the meeting
    :param image_url: URL of the image
    :param embedding: Image description embedding
    """
    try:
        vector_db_client.upsert(
            collection_name="image-description-embeddings",
            wait=True,
            points=[
                models.PointStruct(id=i, 
                            payload={"meeting_id": meeting_id, "image_url": image_url}, 
                            vector=embedding.tolist())
            ]
        )
        logger.info(f"Image description embedding {i} stored successfully")
    except Exception as e:
        logger.error(f"Error storing image description embedding {i}: {e}")


def get_relevant_images(meeting_id, summary_embedding):
    """
    Get relevant images based on the summary embedding.
    
    :param meeting_id: ID of the meeting
    :param summary_embedding: Summary embedding
    :return: Relevant image URLs
    """
    try:
        res = vector_db_client.search(
            collection_name="image-description-embeddings",
            query_vector=summary_embedding.tolist(),
            limit=3,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="meeting_id",
                        match=models.MatchValue(value=meeting_id)
                    )
                ]
            ),
        )
        image_links = [match.payload["image_url"] for match in res]
        logger.info(f"Relevant images retrieved successfully")
    except Exception as e:
        logger.error(f"Error retrieving relevant images: {e}")
        image_links = []
        
    return image_links