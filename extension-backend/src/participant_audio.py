import os
from scipy.io import wavfile
import torch
import numpy as np
from pyannote.audio import Pipeline
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct

"""
Runs independently only once to store voice embeddings of participants from .wav audio clips of 10 seconds 
each stored on your local in the directory specified by VOICE_RECORDINGS_DIR.
The filename should be in the format: <speaker_name>.wav
"""

VOICE_RECORDINGS_DIR = ""

class ParticipantVoiceEmbeddings:
    def __init__(self):
        self.pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.0", use_auth_token=os.getenv("HF_API"))
        self.client = QdrantClient(url=os.getenv("VECTOR_DB_URL"), api_key=os.getenv("VECTOR_DB_API"))
    
    def read_audio_file(self, audio_filepath):
        # read audio file
        self.samplerate, self.data = wavfile.read(audio_filepath)

    def transform_audio(self):
        # audio needs to be converted from stereo to mono
        if len(self.data.shape) == 2:
            self.data = np.mean(self.data, axis=1)
        # convert the data to a torch tensor and add a channel dimension
        self.tensor_data = torch.tensor(self.data).float().unsqueeze(0)

    def create_voice_embedding(self):
        _, self.embedding = self.pipeline({"waveform": self.tensor_data, "sample_rate": self.samplerate}, return_embeddings=True)

    def store_voice_embedding(self, speaker_name, i):
        # insert voice emebdding into vector database
        self.client.upsert(
            collection_name="actual-speaker-embeddings",
            wait=True,
            points=[
                PointStruct(id=i, payload={"speaker": speaker_name}, vector=self.embedding[0].tolist())
            ]
        )

    def voice_embedding_pipeline(self):
        for i, filename in enumerate(os.listdir(VOICE_RECORDINGS_DIR)):
            audio_filepath = os.path.join(VOICE_RECORDINGS_DIR, filename)
            self.read_audio_file(audio_filepath)
            self.transform_audio()
            self.create_voice_embedding()
            self.store_voice_embedding(filename.split(".")[0], i)

# run the pipeline
ParticipantVoiceEmbeddings().voice_embedding_pipeline()