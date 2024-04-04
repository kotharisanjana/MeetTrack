from src.processing.video_processing import VideoProcessing
import common.globals as global_vars
from database.relational_db import insert_image_path
from common.aws_utilities import upload_frame_to_s3

class ImageProcessing:
    def __init__(self, session_data):
        self.local_recording_path = session_data["local_recording_path"]
        self.meeting_id = session_data["meeting_id"]
        self.video_processing_obj = VideoProcessing(self.local_recording_path, self.meeting_id)

    def save_screenshots(self, screenshots):
        for i, frame in enumerate(screenshots):
            image_path = f"{global_vars.SCREENSHOTS_FOLDER}/{self.meeting_id}_screenshot_{i}.png"
            insert_image_path(self.meeting_id, image_path)
            upload_frame_to_s3(frame, image_path)

    def online_image_pipeline(self):
        screenshots = self.video_processing_obj.capture_screenshots()
        self.save_screenshots(screenshots)
