import numpy as np
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_audio
from moviepy.editor import VideoFileClip
from PIL import Image

class VideoProcessing:
    def __init__(self, local_recording_path, meeting_id):
        self.local_recording_path = local_recording_path
        self.meeting_id = meeting_id

    def extract_audio(self, local_audio_path):
        # extracts audio from webm and saves it locally as .wav file
        ffmpeg_extract_audio(self.local_recording_path, local_audio_path)
        
    def capture_screenshots(self, interval=20):
        """
        Captures screenshots from a video file at specified intervals.

        interval: Interval in seconds between each screenshot.
        return: List of images.
        """
        clip = VideoFileClip(self.local_recording_path)
        duration = clip.duration
        screenshots = []

        for i in np.arange(0, duration, interval):
            frame = clip.get_frame(i)  
            img = Image.fromarray(frame)  
            screenshots.append(img)  

        return screenshots

      