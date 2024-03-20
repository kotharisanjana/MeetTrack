import common.globals as global_vars
from io import BytesIO
from PIL import Image
from botocore.exceptions import NoCredentialsError

def upload_frame_to_s3(s3_client, frame, object_name):
    """
    Upload a single frame to S3 bucket.

    :param frame: Numpy array representing an image.
    :param bucket_name: Name of the S3 bucket.
    :param object_name: Object name in S3.
    """
    # Convert the numpy frame to an image in memory
    img = Image.fromarray(frame)
    buffer = BytesIO()
    img.save(buffer, format="PNG") 
    buffer.seek(0)
    # Upload the image to S3
    s3_client.upload_fileobj(buffer, global_vars.S3_BUCKET, object_name)


def get_s3_image_bytes(s3_client, key):
    """
    Fetch an image from an S3 bucket.
    
    :param bucket_name: Name of the S3 bucket
    :param key: Key (path) of the image within the bucket
    :return: Image bytes
    """
    response = s3_client.get_object(Bucket=global_vars.S3_BUCKET, Key=key)
    return response['Body'].read()


def upload_file_to_s3(s3_client, object, object_key):
    """
    Upload a file to an S3 bucket.

    :param file: File to upload.
    :return: True if file was uploaded, else False.
    """
    try:
        s3_client.upload_file(object, global_vars.S3_BUCKET, object_key)
        print(f"File uploaded successfully")
        return True
    except NoCredentialsError:
        print("Credentials not available")
        return False
    except Exception as e:
        print(f"Upload failed: {e}")
        return False


def download_file_from_s3(s3_client, object_key, local_file_path=None):
    """
    Download a file from S3 and return its content as a string.

    :param s3_client: Boto3 S3 client.
    :param object_key: Key of the object to download.
    :return: Content of the downloaded file as a string, or None if download fails.
    """
    try:
        file_content = BytesIO()
        s3_client.download_fileobj(global_vars.S3_BUCKET, object_key, file_content, local_file_path)
        file_content.seek(0)
        file_content_str = file_content.read().decode('utf-8')
        return file_content_str
    except NoCredentialsError:
        print("Credentials not available")
        return None
    except Exception as e:
        print(f"Error downloading file: {e}")
        return None


def get_s3_image_bytes(s3_client, key):
    """
    Fetch an image from an S3 bucket.
    
    :param bucket_name: Name of the S3 bucket
    :param key: Key (path) of the image within the bucket
    :return: Image bytes
    """
    response = s3_client.get_object(Bucket=global_vars.S3_BUCKET, Key=key)
    return response['Body'].read()
