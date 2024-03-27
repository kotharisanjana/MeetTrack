from common.aws_utilities import upload_frame_to_s3
from common.utils import get_intervals
import common.globals as global_vars
from database.relational_db import insert_image_path, fetch_image_path
import numpy as np
import os
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_audio

class VideoProcessing:
    def __init__(self, local_filepath):
        self.local_filepath = local_filepath

    def extract_audio(self):
        ffmpeg_extract_audio(self.local_filepath, os.path.join(global_vars.DOWNLOAD_DIR, "audio.wav"))
        
    # def get_screenshots(self, interval=20):
    #     """
    #     Captures screenshots from a video file at specified intervals.

    #     interval: Interval in seconds between each screenshot.
    #     return: List of images.
    #     """
    #     duration = self.clip.duration
    #     screenshots = []

    #     for i in np.arange(0, duration, interval):
    #         video_timestamp = get_intervals(i)
    #         frame = self.clip.get_frame(i)
    #         screenshots.append(frame)

    #         image_identifier = f"screenshot_{video_timestamp}.png"
    #         insert_image_path(image_identifier)
    #         object_name = fetch_image_path()
    #         upload_frame_to_s3(frame, object_name)