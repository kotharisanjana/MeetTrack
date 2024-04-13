from src.processing.video_processing import VideoProcessing
import common.globals as global_vars
from database.relational_db import insert_image_path
from common.aws_utilities import upload_frame_to_s3

class ImageProcessing:
    def __init__(self, session_data):
        self.local_recording_path = session_data["local_recording_path"]
        self.meeting_id = session_data["meeting_id"]
        self.video_processing_obj = VideoProcessing(self.local_recording_path, self.meeting_id)

    def save_screenshots(self, frames):
        for frame in frames:
            images_recording_index = str(global_vars.IMAGES_GLOBAL_INDEX)
            image_path = f"{global_vars.SCREENSHOTS_FOLDER}/{str(self.meeting_id)}_screenshot_{images_recording_index}.png"

            insert_image_path(self.meeting_id, image_path)
            upload_frame_to_s3(frame, image_path)

            global_vars.IMAGES_GLOBAL_INDEX = global_vars.IMAGES_GLOBAL_INDEX + 1

    def online_image_pipeline(self):
        frames = self.video_processing_obj.capture_screenshots()
        self.save_screenshots(frames)
