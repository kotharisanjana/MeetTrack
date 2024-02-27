from setup import setup_obj

class TextEmbedding:
    def create_text_embedding(self, segment):
        segment_embedding = setup_obj.embedding_model.embed_query(segment)
        return segment_embedding

    