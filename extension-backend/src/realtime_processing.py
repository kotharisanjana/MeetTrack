from src.asr import ASR
from src.diarization import SpeakerDiarization, SpeakerIDsForTranscription
from src.video_processing import VideoProcessing
from src.transcript import combine_asr_diarization
from common.aws_utilities import upload_file_to_s3, download_textfile_from_s3
from database.vector_db import fetch_curr_transcript_path

class RealtimeAudio:
    def __init__(self, meeting_recording):
        self.meeting_recording = meeting_recording
        
    def realtime_audio_pipeline(self):
        video_processing_obj = VideoProcessing(self.meeting_recording)
        meeting_audio = video_processing_obj.get_audio()

        # transcription
        asr_obj = ASR(meeting_audio)
        asr_obj.asr_pipeline()

        # diarization
        diarization_obj = SpeakerDiarization(meeting_audio)
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