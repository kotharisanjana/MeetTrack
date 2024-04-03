from common.utils import get_unixtime
from __init__ import diarization_pipeline
from database.vector_db import store_speaker_embedding
import torch
import numpy as np
from scipy.io import wavfile

class SpeakerDiarization:
    def __init__(self, meeting_id, local_audio_path, local_diarization_path):
        self.meeting_id = meeting_id
        self.local_audio_path = local_audio_path
        self.local_diarization_path = local_diarization_path

    def read_meeting_audio(self):
        self.samplerate, self.data = wavfile.read(self.local_audio_path)

    def transform_audio(self):
    # audio needs to be converted from stereo to mono
        if len(self.data.shape) == 2:
            self.data = np.mean(self.data, axis=1)
        # Convert the data to a torch tensor and add a channel dimension
        self.tensor_data = torch.tensor(self.data).float().unsqueeze(0)

    def diarize(self):
        self.speakers, self.embeddings = diarization_pipeline({"waveform": self.tensor_data, "sample_rate": self.samplerate}, return_embeddings=True)

    def diarization_pipeline(self):
        self.read_meeting_audio()
        self.transform_audio()
        self.diarize()
        store_speaker_embedding(self.embeddings)

    def create_diarization(self):
        with open(self.local_diarization_path, "a") as file:
           file.write(str(self.speakers) + "\n")
           file.write("*" + "\n")


class Speaker:
    def __init__(self, speaker_id):
        self.speaker_id = speaker_id


class SpeakerIdentification:
    def __init__(self, start_time, end_time, speaker):
        self.start_time = start_time
        self.end_time = end_time
        self.speaker = speaker
        

class SpeakerIDsForTranscription:
    def extract_time_info(self, time_string):
        time_components = time_string.split(":")
        hour = time_components[0]
        min = time_components[1]
        sec = time_components[2][:2]
        millisec = time_components[2][-3:]
        return int(hour), int(min), int(sec), int(millisec)

    def create_speaker_segments(self, local_diarization_path):
        self.speaker_segments = []

        with open(local_diarization_path, "r") as file:
            for line in file:
                if len(line) < 2:
                    continue

                segment_components = line.split()

                start = segment_components[1]
                start_hour, start_min, start_sec, start_millisec  = self.extract_time_info(start)
                end = segment_components[3][:-1]
                end_hour, end_min, end_sec, end_millisec  = self.extract_time_info(end)

                # convert start and end time to datetime
                start_time = get_unixtime(start_hour, start_min, start_sec, start_millisec)
                end_time = get_unixtime(end_hour, end_min, end_sec, end_millisec)

                # to handle incorrect diarization where a slight change in tone of the existing speaker is changing speaker id -> error
                if end_time - start_time < 1:
                    continue

                speaker = Speaker(segment_components[5].split("_")[1])
                speaker_identification_obj = SpeakerIdentification(start_time, end_time, speaker)
                self.speaker_segments.append(speaker_identification_obj)

    def merge_speaker_segments(self):
        l = len(self.speaker_segments)
        i = 0
        speaker_duration = []

        while i<l:
            start_time = self.speaker_segments[i].start_time
            end_time = self.speaker_segments[i].end_time
            speaker = self.speaker_segments[i].speaker.speaker_id

            j = i
            while j<l and self.speaker_segments[j].speaker.speaker_id==speaker:
                j += 1

            if i!=j:
                end_time = self.speaker_segments[j-1].end_time

            speaker_duration.append(SpeakerIdentification(start_time, end_time, Speaker(speaker)))

            i = j

        return speaker_duration

    def speaker_segments_pipeline(self, local_diarization_path):
        self.create_speaker_segments(local_diarization_path)
        return self.merge_speaker_segments()
