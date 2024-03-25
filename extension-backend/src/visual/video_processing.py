from common.aws_utilities import upload_frame_to_s3
from common.utils import get_intervals
from database.vector_db import insert_image_path, fetch_image_path
from moviepy.editor import VideoFileClip
import numpy as np

class VideoProcessing:
    def __init__(self, meeting_recording):
        self.clip = VideoFileClip(meeting_recording)

    def get_audio(self):
        return self.clip.audio
        
    def get_screenshots(self, interval=20):
        """
        Captures screenshots from a video file at specified intervals.

        interval: Interval in seconds between each screenshot.
        return: List of images.
        """
        duration = self.clip.duration
        screenshots = []

        for i in np.arange(0, duration, interval):
            video_timestamp = get_intervals(i)
            frame = self.clip.get_frame(i)
            screenshots.append(frame)

            image_identifier = f"screenshot_{video_timestamp}.png"
            insert_image_path(image_identifier)
            object_name = fetch_image_path()
            upload_frame_to_s3(frame, object_name)