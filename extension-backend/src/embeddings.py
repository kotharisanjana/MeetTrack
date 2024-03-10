import os
from scipy.io import wavfile
import torch
import numpy as np
from flask import current_app

class VoiceEmbeddings:
    def read_audio_file(self, audio_file_path):
        self.init_obj = current_app.config["init_obj"]
        self.vector_store_obj = current_app.config["vector_store_obj"]
        self.samplerate, self.data = wavfile.read(audio_file_path)

    def transform_audio(self):
        # audio needs to be converted from stereo to mono
        if len(self.data.shape) == 2:
            self.data = np.mean(self.data, axis=1)
        # Convert the data to a torch tensor and add a channel dimension
        self.tensor_data = torch.tensor(self.data).float().unsqueeze(0)

    def create_audio_embedding(self):
        _, self.voice_embedding = self.init_obj.pipeline({"waveform": self.tensor_data, "sample_rate": self.samplerate}, return_embeddings=True)

    def actual_audio_embedding_pipeline(self):
        # iterate through all speaker voice files
        for filename in os.listdir(self.init_obj.ACTUAL_AUDIO_PATH):
            audio_file_path = os.path.join(self.ACTUAL_AUDIO_PATH, filename)
            self.read_audio_file(audio_file_path)
            self.transform_audio()
            self.create_audio_embedding()
            self.vector_store_obj.store_voice_embedding(filename.split(".")[0], self.voice_embedding)


def create_text_embedding(segment):
    segment_embedding = current_app.config["init_obj"].embedding_model.embed_query(segment)
    return segment_embedding 