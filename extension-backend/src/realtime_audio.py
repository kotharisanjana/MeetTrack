from src.asr import ASR
from src.diarization import SpeakerDiarization, SpeakerIDsForTranscription
from src.extract_audio import ExtractAudio
from src.final_transcript import combine_asr_diarization

class RealtimeAudio:
    def __init__(self, meeting_recording, session_id, vector_db_obj):
        self.meeting_recording = meeting_recording
        self.meeting_chunk = 0
        self.output = ""
        self.vector_db_obj = vector_db_obj
        self.session_id = session_id
        
    def realtime_audio_pipeline(self):
        meeting_audio = ExtractAudio(self.meeting_recording).video_to_audio_pipeline()

        # transcription
        asr_obj = ASR(meeting_audio, self.session_id)
        asr_obj.asr_pipeline()

        # diarization
        diarization_obj = SpeakerDiarization(meeting_audio, self.sesison_id)
        diarization_obj.diarization_pipeline()

        # merge transcription and diarization and get actual speakers
        diarization = diarization_obj.get_speakers()
        speakers_obj = SpeakerIDsForTranscription(diarization)
        speakers_obj.merge_speaker_segments_pipeline()

        audio_to_text_output = combine_asr_diarization(speakers_obj.speaker_segments, asr_obj.transcript_segments, self.vector_db_obj)

        self.output = self.output + audio_to_text_output + "\n"

        # with open(self.init_obj.OUTPUT_TRANSCRIPT_FILE, "a") as text_file:
        #   text_file.write(str(self.output))

        self.meeting_chunk += 1