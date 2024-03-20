from src.asr import ASR
from src.diarization import SpeakerDiarization, SpeakerIDsForTranscription
from src.extract_audio import ExtractAudio
from src.final_transcript import combine_asr_diarization
from common.aws_utilities import upload_file_to_s3, download_file_from_s3

class RealtimeAudio:
    def __init__(self, meeting_recording, session_data):
        self.meeting_recording = meeting_recording
        self.session_data = session_data
        
    def realtime_audio_pipeline(self):
        meeting_audio = ExtractAudio(self.meeting_recording).video_to_audio_pipeline()

        # transcription
        asr_obj = ASR(meeting_audio, self.session_data["session_id"])
        asr_obj.asr_pipeline()

        # diarization
        diarization_obj = SpeakerDiarization(meeting_audio, self.session_data["session_id"])
        diarization_obj.diarization_pipeline()

        # merge transcription and diarization and get actual speakers
        diarization = diarization_obj.get_speakers()
        speakers_obj = SpeakerIDsForTranscription(diarization)
        speakers_obj.merge_speaker_segments_pipeline()

        audio_to_text_output = combine_asr_diarization(speakers_obj.speaker_segments, asr_obj.transcript_segments, self.session_data["vector_db_obj"])

        
        transcript_path = self.session_data["relational_db_obj"].fetch_curr_transcript_path()
        # download existing transcript and append new transcript
        transcript = download_file_from_s3(self.session_data["s3_client"], transcript_path)
        transcript = transcript + audio_to_text_output + "\n"
        # upload transcript back to s3
        upload_file_to_s3(self.session_data["s3_client"], transcript+".txt", transcript_path)