import moviepy.editor as moviepy

class ExtractAudio:
    def __init__(self, meeting_recording):
        self.meeting_recording = meeting_recording

    def extract_audio(self):
        self.clip = moviepy.VideoFileClip(self.meeting_recording)

    def get_wav_file(self):
        return self.clip.audio

    def video_to_audio_pipeline(self):
        self.extract_audio()
        return self.get_wav_file()