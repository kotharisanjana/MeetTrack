from init import setup_obj

import numpy as np

class VectorStore():
    def create_index(self):
        self.db_audio_index = setup_obj.db_audio.Index("speaker-voices")
        self.db_transcript_index = setup_obj.db_transcript.Index("transcripts")

    def get_actual_speaker(self, speaker_id):
        record = self.db_audio_index.fetch(ids=[speaker_id], namespace="identified_speaker_embeddings")
        speaker_embedding = record["vectors"][speaker_id]["values"]

        speaker_match = self.db_audio_index.query(
            vector = speaker_embedding,
            top_k=1,
            namespace="actual_speaker_embeddings"
        )
        actual_speaker = speaker_match["matches"][0]["id"]
        return actual_speaker
    
    def store_text_embedding(self, meeting_chunk, segment, segment_embedding):
        self.db_transcript_index.upsert(
            vectors=[
                {"id":setup_obj.MEETING_NAME + "_" + setup_obj.MEETING_DATE + "_" +str(meeting_chunk), 
                "values":segment_embedding,
                "metadata":{
                    "segment_text": segment,
                    "meeting_name": setup_obj.MEETING_NAME,
                    "meeting_date": setup_obj.MEETING_DATE}
                }
                ],
            namespace="transcript_embeddings"
        )

    def get_nearest_segments(self, query_embedding):
        query_match = self.db_transcript_index.query(
            vector = query_embedding,
            top_k=3,
            namespace="transcript_embeddings",
            filter={
              "meeting_name": setup_obj.MEETING_NAME,
              },
            include_metadata=True
        )
        segments = query_match["matches"]
        return segments

    def store_speaker_embedding(self, embeddings):
        for i, emb in enumerate(embeddings):
            if np.any(emb):
                self.db_audio_index.upsert(
                    vectors=[
                        {"id":str(i), "values":emb.tolist()}
                    ],
                    namespace="identified_speaker_embeddings"
                )

    def store_voice_embedding(self, speaker_name, voice_embedding):
        self.db_audio_index.upsert(
            vectors=[
                {"id":speaker_name, 
                 "values":voice_embedding[0].tolist()
                }
            ],
            namespace="actual_speaker_embeddings"
        )