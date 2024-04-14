from __init__ import llm_vision, embedding_model, logger
from database.vector_db import store_description_embedding, get_relevant_images
from database.relational_db import fetch_image_paths
from common.aws_utilities import download_file_from_s3

from langchain_core.messages import HumanMessage
import os

class VisualComponent:
    def __init__(self, meeting_id):
        self.meeting_id = meeting_id

    def get_image_urls(self):
        # get list of image url for the current meeting from S3
        self.image_urls = fetch_image_paths(self.meeting_id)

    def generate_image_descriptions(self, local_images_path):
        self.descriptions = {}

        for image_url in self.image_urls:
            local_path = os.path.join(local_images_path, image_url.split("/")[-1])
            download_file_from_s3(image_url, local_path)
            try:
                message = HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": "Describe the image in 2-3 lines. Give an overview of what the whole image talks about",
                        },
                        {
                            "type": "image_url", 
                            "image_url": local_path
                        },
                    ]
                )

                response = llm_vision.invoke([message])
                self.descriptions[image_url] = response.content
            except Exception as e:
                self.descriptions[image_url] = "Error retrieving description for this image"
                logger.error(f"Error generating description for image {image_url}: {e}")

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
        image_desc_pairs = {}
        for img in image_urls:
            image_desc_pairs[img] = self.descriptions[img]

        return image_desc_pairs
    
    def get_contextual_images_from_summary(self, summary, local_images_path):
        self.get_image_urls()
        self.generate_image_descriptions(local_images_path)
        self.image_description_embedding()
        summary_embedding = self.create_embedding(summary)
        image_urls = get_relevant_images(self.meeting_id, summary_embedding)
        return self.image_url_description_pairs(image_urls)
