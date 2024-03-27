from src.audio_to_text.asr import ASR
from src.audio_to_text.diarization import SpeakerDiarization, SpeakerIDsForTranscription
from src.processing.video_processing import VideoProcessing
import common.globals as global_vars
from src.audio_to_text.transcript import combine_asr_diarization
from common.aws_utilities import upload_file_to_s3, download_textfile_from_s3
from database.relational_db import fetch_curr_transcript_path
from scipy.io import wavfile
import os

class RealtimeAudio:
    def realtime_audio_pipeline(self, local_filepath):
        VideoProcessing(local_filepath).extract_audio()

        # transcription
        asr_obj = ASR(os.path.join(global_vars.DOWNLOAD_DIR, "audio.wav"))
        asr_obj.asr_pipeline()

        # diarization
        diarization_obj = SpeakerDiarization(os.path.join(global_vars.DOWNLOAD_DIR, "audio.wav"))
        diarization_obj.diarization_pipeline()

        # merge transcription and diarization and get actual speakers
        diarization = diarization_obj.get_speakers()
        speakers_obj = SpeakerIDsForTranscription(diarization)
        speakers_obj.merge_speaker_segments_pipeline()

        audio_to_text_output = combine_asr_diarization(speakers_obj.speaker_segments, asr_obj.transcript_segments)

        transcript_path = fetch_curr_transcript_path()
        # download existing transcript and append new transcript
        transcript = download_textfile_from_s3(transcript_path)
        transcript = transcript + audio_to_text_output + "\n"
        # upload transcript back to s3
        upload_file_to_s3(transcript+".txt", transcript_path)