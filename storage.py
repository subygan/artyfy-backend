import os
import boto3
from botocore.exceptions import NoCredentialsError
import uuid
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from flask import current_app

# Load environment variables
load_dotenv()

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('S3_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('S3_SECRET_KEY'),
    region_name=os.getenv('S3_REGION'),
    endpoint_url=os.getenv('S3_ENDPOINT')
)

def upload_file(file_data, filename=None, content_type='image/jpeg'):
    """
    Upload a file to S3 bucket
    
    Args:
        file_data (bytes): File data to upload
        filename (str, optional): Name to use for the file. If None, a random name will be generated
        content_type (str, optional): MIME type of the file. Defaults to 'image/jpeg'
        
    Returns:
        str: URL of the uploaded file, or None if upload failed
    """
    if filename is None:
        # Generate a unique filename
        extension = 'jpg' if content_type == 'image/jpeg' else 'png'
        filename = f"{uuid.uuid4()}.{extension}"
    else:
        # Secure the filename
        filename = secure_filename(filename)
    
    bucket_name = os.getenv('S3_BUCKET_NAME')
    
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=file_data,
            ContentType=content_type
        )
        
        # Generate URL for the uploaded file
        s3_endpoint = os.getenv('S3_ENDPOINT')
        return f"{s3_endpoint}/{bucket_name}/{filename}"
    
    except NoCredentialsError:
        current_app.logger.error("S3 credentials not available")
        return None
    except Exception as e:
        current_app.logger.error(f"Error uploading file to S3: {str(e)}")
        return None

def download_file(file_url):
    """
    Download a file from S3 bucket
    
    Args:
        file_url (str): Full URL of the file to download
        
    Returns:
        bytes: File data, or None if download failed
    """
    if not file_url:
        return None
    
    bucket_name = os.getenv('S3_BUCKET_NAME')
    
    try:
        # Extract file name from URL
        filename = file_url.split('/')[-1]
        
        response = s3_client.get_object(
            Bucket=bucket_name,
            Key=filename
        )
        
        return response['Body'].read()
    
    except Exception as e:
        current_app.logger.error(f"Error downloading file from S3: {str(e)}")
        return None

def delete_file(file_url):
    """
    Delete a file from S3 bucket
    
    Args:
        file_url (str): Full URL of the file to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    if not file_url:
        return False
    
    bucket_name = os.getenv('S3_BUCKET_NAME')
    
    try:
        # Extract file name from URL
        filename = file_url.split('/')[-1]
        
        s3_client.delete_object(
            Bucket=bucket_name,
            Key=filename
        )
        
        return True
    
    except Exception as e:
        current_app.logger.error(f"Error deleting file from S3: {str(e)}")
        return False
