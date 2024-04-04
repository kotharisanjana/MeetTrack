from __init__ import llm_vision, embedding_model
from database.vector_db import store_description_embedding, get_relevant_images
from database.relational_db import fetch_image_path

class VisualComponent:
    def __init__(self, meeting_id):
        self.meeting_id = meeting_id

    def get_image_urls(self):
        self.image_urls = fetch_image_path(self.meeting_id)

    def generate_image_descriptions(self):
        self.descriptions = {}

        for image_url in self.image_urls:
            try:
                response = llm_vision.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "What is in this image? Describe it in 3 lines"},
                                {"type": "image_url", "image_url": {"url": image_url}},
                            ],
                        }
                    ],
                    max_tokens=300,
                )

                desc = response.choices[0].message.content
                self.descriptions[image_url] = desc.strip()
            except Exception as e:
                print(f"Error processing {image_url}: {e}")
                self.descriptions[image_url] = "Error retrieving description for this image"

    def create_embedding(self, text):
        embedding = embedding_model.encode(text)
        return embedding    

    def image_description_embedding(self):
        idx = 0
        for image_url, desc in self.descriptions.items():
            embedding = self.create_embedding(desc)
            store_description_embedding(idx, self.meeting_id, image_url, embedding)
            idx += 1

    def image_url_description_pairs(self, image_urls):
        return dict((image_url, self.descriptions[image_url]) for image_url in image_urls)

    def get_contextual_images_from_summary(self, summary):
        self.get_image_urls()
        self.generate_image_descriptions()
        self.image_description_embedding()
        summary_embedding = self.create_embedding(summary)
        image_urls = get_relevant_images(summary_embedding)
        return self.image_url_description_pairs(image_urls)
