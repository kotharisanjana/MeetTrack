import moviepy.editor as moviepy

class ExtractAudio:
    def __init__(self, video_file, audio_file):
        # audio and video file paths in s3
        self.video_file = video_file
        self.audio_file = audio_file

    def extract_audio(self):
        self.clip = moviepy.VideoFileClip(self.video_file)

    def save_audio(self):
        self.clip.audio.write_audiofile(self.audio_file)

    def video_to_audio_pipeline(self):
        self.extract_audio()
        self.save_audio()
