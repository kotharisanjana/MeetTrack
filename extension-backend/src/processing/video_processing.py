from __init__ import logger

from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_audio
import cv2

class VideoProcessing:
    def __init__(self, local_recording_path, meeting_id):
        self.local_recording_path = local_recording_path
        self.meeting_id = meeting_id

    def extract_audio(self, local_audio_path):
        # extract audio from webm and saves it locally as .wav file
        ffmpeg_extract_audio(self.local_recording_path, local_audio_path)
        
    def capture_screenshots(self, duration=30, interval=5):
        """
        Captures screenshots from a video file at specified intervals.

        interval: Interval in seconds between each screenshot.
        return: List of images.
        """        
        cap = cv2.VideoCapture(self.local_recording_path)

        if not cap.isOpened():
            logger.error("Error opening video file")
            return None
        
        frames_to_capture = duration/interval

        frames = []

        # read and store the frames
        count = 0
        while cap.isOpened() and count < frames_to_capture:
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
                count += 1
            else:
                break

        cap.release()

        return frames

      