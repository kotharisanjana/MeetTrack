from asr import ASR
from diarization import SpeakerDiarization, SpeakerIDsForTranscription
from extract_audio import ExtractAudio
from final_transcript import combine_asr_diarization
from embeddings import create_text_embedding
from setup import setup_obj, vector_db_obj


class RealtimeAudio:
    def __init__(self, video_file, audio_file):
        self.video_file = video_file
        self.audio_file = audio_file
        self.meeting_chunk = 0
        self.output = ""
        
    def realtime_audio_pipeline(self):
        extract_audio_obj = ExtractAudio(self.video_file, self.audio_file)
        extract_audio_obj.video_to_audio_pipeline()

        audio = extract_audio_obj.clip.audio

        # transcription
        asr_obj = ASR(audio)
        asr_obj.asr_pipeline()

        # diarization
        diarization_obj = SpeakerDiarization(audio)
        diarization_obj.diarization_pipeline()

        # merge transcription and diarization and get actual speakers
        diarization = diarization_obj.get_speakers()
        speakers_obj = SpeakerIDsForTranscription(diarization)
        speakers_obj.merge_speaker_segments_pipeline()
        audio_to_text_output = combine_asr_diarization(speakers_obj.speaker_segments, asr_obj.transcript_segments)

        # create transcript segment embeddings and store in vector store
        audio_to_text_embedding = create_text_embedding(audio_to_text_output)
        vector_db_obj.store_text_embedding(self.meeting_chunk, audio_to_text_output, audio_to_text_embedding)

        self.output = self.output + audio_to_text_output + "\n"

        with open(setup_obj.OUTPUT_TRANSCRIPT_FILE, "a") as text_file:
          text_file.write(str(self.output))

        self.meeting_chunk += 1