from common.aws_utilities import upload_file_to_s3
from database.relational_db import insert_recording_path, fetch_recording_path
from src.processing.meeting_start import audio_processing_obj, image_processing_obj

def save_recording(meeting_recording, meeting_id, local_recording_path):
    # save meeting recording to local file system
    meeting_recording.save(local_recording_path)
    # upload meeting recording to S3 and store path in relational database
    insert_recording_path(meeting_id)
    recording_path = fetch_recording_path(meeting_id)
    upload_file_to_s3(local_recording_path, recording_path)


def process_recording():
    # process transcription, diarization and screenshots for recorded segment
    audio_processing_obj.online_audio_pipeline() 
    image_processing_obj.online_image_pipeline()
