#upload to s3
from io import BytesIO
import boto3
from PIL import Image
from botocore.exceptions import NoCredentialsError


# s3 = boto3.client("s3")
bucket_name = ""
object_key = ""
local_file_path = ""

def upload_frame_to_s3(frame, bucket_name, object_name):
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
    s3 = boto3.client('s3')
    s3.upload_fileobj(buffer, bucket_name, object_name)

def get_s3_image_bytes(bucket_name, key):
    """
    Fetch an image from an S3 bucket.
    
    :param bucket_name: Name of the S3 bucket
    :param key: Key (path) of the image within the bucket
    :return: Image bytes
    """
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket_name, Key=key)
    return response['Body'].read()

def upload_file_to_s3(file_name, bucket_name, object_name):
    """
    Upload a file to an S3 bucket.

    :param file_name: File to upload.
    :param bucket_name: Bucket to upload to.
    :param object_name: S3 object name. If not specified, file_name is used.
    :return: True if file was uploaded, else False.
    """
    # Create an S3 client
    s3_client = boto3.client('s3')

    try:
        # Upload the file
        s3_client.upload_file(file_name, bucket_name, object_name)
        print(f"File {file_name} uploaded to {bucket_name}/{object_name}")
        return True
    except NoCredentialsError:
        print("Credentials not available")
        return False
    except Exception as e:
        print(f"Upload failed: {e}")
        return False



def download_file_from_s3(bucket_name, object_key, local_file_path):
    """
    Download a file from S3 to a local file path.

    :param bucket_name: Name of the S3 bucket.
    :param object_key: Key of the object to download.
    :param local_file_path: Local path to save the downloaded file.
    """
    s3 = boto3.client('s3')
    try:
        s3.download_file(bucket_name, object_key, local_file_path)
        print(f"File downloaded successfully to {local_file_path}")
    except NoCredentialsError:
        print("Credentials not available")
    except Exception as e:
        print(f"Error downloading file: {e}")

def get_s3_image_bytes(bucket_name, key):
    """
    Fetch an image from an S3 bucket.
    
    :param bucket_name: Name of the S3 bucket
    :param key: Key (path) of the image within the bucket
    :return: Image bytes
    """
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket_name, Key=key)
    return response['Body'].read()
