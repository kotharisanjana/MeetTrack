import numpy as np
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_audio
from moviepy.editor import VideoFileClip
import subprocess

class VideoProcessing:
    def __init__(self, local_recording_path, meeting_id):
        self.local_recording_path = local_recording_path
        self.meeting_id = meeting_id

    def extract_audio(self, local_audio_path):
        # extract audio from webm and saves it locally as .wav file
        ffmpeg_extract_audio(self.local_recording_path, local_audio_path)
        
    def capture_screenshots(self, interval=20):
        """
        Captures screenshots from a video file at specified intervals.

        interval: Interval in seconds between each screenshot.
        return: List of images.
        """
        # convert webm to mp4
        mp4_path = self.local_recording_path.replace("webm", "mp4")

        ffmpeg_command = [
            "ffmpeg",
            "-i",
            self.local_recording_path,
            mp4_path,
            "-speed",
            "16"
        ]
        subprocess.run(ffmpeg_command) 

        # capture frames from mp4 in given interval
        clip = VideoFileClip(mp4_path)
        duration = clip.duration
        screenshots = []

        for i in np.arange(0, duration, interval):
            img = clip.get_frame(i)
            screenshots.append(img)  

        return screenshots

      