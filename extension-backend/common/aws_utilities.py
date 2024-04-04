import common.globals as global_vars
from __init__ import s3_client, logger

from io import BytesIO
from PIL import Image

# ------------------- Uploads -------------------

def upload_frame_to_s3(object, object_key):
    """
    Upload a single frame to S3 bucket.

    :param object: Numpy array representing an image.
    :param object_key: Key of the object in the bucket.
    :return: True if frame was uploaded, else False.
    """
    # Convert the numpy frame to an image in memory
    img = Image.fromarray(object)
    buffer = BytesIO()
    img.save(buffer, format="PNG") 
    buffer.seek(0)

    # Upload the image to S3
    try:
        s3_client.upload_fileobj(buffer, global_vars.S3_BUCKET, object_key)
        logger.info(f"Frame {object_key} uploaded successfully")
        return True
    except Exception as e:
        logger.error(f"Frame {object_key} upload failed: {e}")
        return False


def upload_file_to_s3(object, object_key):
    """
    Upload a file to S3 bucket.

    :param object: File to upload.
    :param object_key: Key of the object in the bucket.
    :return: True if file was uploaded, else False.
    """
    try:
        s3_client.upload_file(object, global_vars.S3_BUCKET, object_key)
        logger.info(f"File {object_key} uploaded successfully")
        return True
    except Exception as e:
        logger.error(f"File {object_key} upload failed: {e}")
        return False

# ------------------- Downloads -------------------
    
def get_s3_image_bytes(object_key):
    """
    Fetch an image from S3 bucket.
    
    :param object_key: Key of the object in the bucket
    :return: Image bytes
    """
    try:
        response = s3_client.get_object(Bucket=global_vars.S3_BUCKET, Key=object_key)
        logger.info(f"Image {object_key} fetched successfully")
        return response['Body'].read()
    except Exception as e:
        logger.error(f"Image {object_key} fetch failed: {e}")
        return None


def download_file_from_s3(object_key, local_filepath):
    """
    Download a file from S3 to a local file path.

    :param object_key: Key of the object to download.
    :param local_filepath: Local path to save the downloaded file.
    :return: True if file was downloaded, else False.
    """
    try:
        s3_client.download_file(global_vars.S3_BUCKET, object_key, local_filepath)
        logger.info(f"File {object_key} downloaded successfully")
        return True
    except Exception as e:
        logger.error(f"File {object_key} download failed: {e}")
        return False
        

