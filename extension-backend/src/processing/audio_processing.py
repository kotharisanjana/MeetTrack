from src.audio_to_text.asr import ASR
from src.audio_to_text.diarization import SpeakerDiarization, SpeakerIDsForTranscription
from src.processing.video_processing import VideoProcessing
from src.audio_to_text.transcript import combine_asr_diarization
from database.relational_db import fetch_curr_transcript_path, fetch_diarization_path
from common.aws_utilities import upload_file_to_s3
import common.globals as global_vars

class AudioProcessing:
    def __init__(self, session_data):
        self.local_recording_path = session_data["local_recording_path"]
        self.meeting_id = session_data["meeting_id"]
        self.local_audio_path = session_data["local_audio_path"]
        self.local_diarization_path = session_data["local_diarization_path"]
        self.local_transcript_path = session_data["local_transcript_path"]

        self.asr_obj = ASR(self.meeting_id, self.local_transcript_path)
        self.diarization_obj = SpeakerDiarization(self.meeting_id, self.local_audio_path, self.local_diarization_path)
        self.video_processing_obj = VideoProcessing(self.local_recording_path, self.meeting_id)

    def online_audio_pipeline(self):
        self.video_processing_obj.extract_audio(self.local_audio_path)

        self.transcript_path = fetch_curr_transcript_path(self.meeting_id)

        # transcription
        self.asr_obj.transcribe(self.local_audio_path)
        self.asr_obj.create_transcript(self.transcript_path)
        # diarization
        self.diarization_obj.diarization_pipeline()
        self.diarization_obj.create_diarization()

    def offline_audio_pipeline(self):
        # upload diarization file to S3 for backup
        diarization_path = fetch_diarization_path(self.meeting_id)
        upload_file_to_s3(self.local_diarization_path, diarization_path)

        transcript_fp_start = 0
        diarization_fp_start = 0
        audio_to_text_output = ""

        # merge transcription and diarization and get actual speakers for every recording segment
        while global_vars.RECORDING_GLOBAL_INDEX > 0:
            transcript_segments, transcript_fp_start = self.asr_obj.create_transcript_segments(transcript_fp_start)
            speaker_segments, diarization_fp_start = SpeakerIDsForTranscription().speaker_segments_pipeline(self.local_diarization_path, diarization_fp_start)
            audio_to_text_output = audio_to_text_output + combine_asr_diarization(speaker_segments, transcript_segments) + "\n"
            global_vars.RECORDING_GLOBAL_INDEX = global_vars.RECORDING_GLOBAL_INDEX - 1

        # update transcript file in local filesystem with final transcript with actual speakers
        with open(self.local_transcript_path, "w") as file:
            file.write(audio_to_text_output)
        # upload final transcript to s3
        upload_file_to_s3(self.local_transcript_path, self.transcript_path)

        
