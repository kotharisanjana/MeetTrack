from src.audio_to_text.asr import ASR
from src.audio_to_text.diarization import SpeakerDiarization, SpeakerIDsForTranscription
from src.processing.video_processing import VideoProcessing
import common.globals as global_vars
from src.audio_to_text.transcript import combine_asr_diarization
from database.relational_db import fetch_curr_transcript_path, fetch_diarization_path
import os

class OnlineAudioProcessing:
    def __init__(self, local_filepath, meeting_id):
        self.local_filepath = local_filepath
        self.meeting_id = meeting_id

    def audio_pipeline(self):
        VideoProcessing(self.local_filepath, self.meeting_id).extract_audio()

        transcript_path = fetch_curr_transcript_path(self.meeting_id)
        # diarization_path = fetch_diarization_path(self.meeting_id)

        # transcription
        asr_obj = ASR(self.meeting_id)
        asr_obj.transcribe(os.path.join(global_vars.DOWNLOAD_DIR, f"{self.meeting_id}_audio.wav"))
        print("ask a question now")
        asr_obj.create_transcript(transcript_path)

        # diarization
        diarization_obj = SpeakerDiarization(os.path.join(global_vars.DOWNLOAD_DIR, f"{self.meeting_id}_audio.wav"), self.meeting_id)
        diarization_obj.diarization_pipeline()
        diarization_obj.create_diarization()

        # merge transcription and diarization and get actual speakers
        # call transcript_segments function
        
        # speakers_obj = SpeakerIDsForTranscription(diarization)
        # speakers_obj.speaker_segments_pipeline()

        # audio_to_text_output = combine_asr_diarization(speakers_obj.speaker_segments, asr_obj.transcript_segments)

        #  # upload transcript back to s3
        # upload_file_to_s3(os.path.join(global_vars.DOWNLOAD_DIR, f"{self.meeting_id}_transcript.txt"), transcript_path)

        # upload transcript back to s3
        # upload_file_to_s3(os.path.join(global_vars.DOWNLOAD_DIR, f"{meeting_id}_diarization.txt"), diarization_path)

        
