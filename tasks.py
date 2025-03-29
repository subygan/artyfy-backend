import os
from celery import Celery
from PIL import Image as PILImage
from PIL import ImageOps, ImageFilter, ImageEnhance
import io
import json
import uuid
from datetime import datetime
import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Initialize Celery
celery_app = Celery('artyfy')
celery_app.conf.broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
celery_app.conf.result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('S3_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('S3_SECRET_KEY'),
    region_name=os.getenv('S3_REGION'),
    endpoint_url=os.getenv('S3_ENDPOINT')
)

# Import models here to avoid circular imports
from models import db, ProcessingStatus, FilteredImage, FilterJob, Filter, Image
from app import app

def upload_to_s3(file_data, file_name):
    """Upload a file to S3 bucket"""
    bucket_name = os.getenv('S3_BUCKET_NAME')
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=file_data,
            ContentType='image/jpeg'
        )
        return f"{os.getenv('S3_ENDPOINT')}/{bucket_name}/{file_name}"
    except NoCredentialsError:
        print("S3 credentials not available")
        return None
    except Exception as e:
        print(f"Error uploading to S3: {str(e)}")
        return None

def download_from_s3(file_url):
    """Download a file from S3 bucket"""
    bucket_name = os.getenv('S3_BUCKET_NAME')
    if not file_url:
        return None
    
    try:
        # Extract file name from URL
        file_name = file_url.split('/')[-1]
        response = s3_client.get_object(Bucket=bucket_name, Key=file_name)
        return response['Body'].read()
    except Exception as e:
        print(f"Error downloading from S3: {str(e)}")
        return None

def apply_filter(image_data, filter_settings):
    """Apply filter effects to an image based on settings"""
    if not image_data:
        return None
    
    try:
        # Open image
        img = PILImage.open(io.BytesIO(image_data))
        
        # Apply filter based on settings
        filter_type = filter_settings.get('type', '')
        
        if filter_type == 'grayscale':
            img = ImageOps.grayscale(img)
            # Convert back to RGB for consistent saving
            img = PILImage.merge('RGB', [img, img, img])
        
        elif filter_type == 'sepia':
            sepia_filter = lambda x: tuple(
                int(min(255, x[0] * 0.393 + x[1] * 0.769 + x[2] * 0.189)),
                int(min(255, x[0] * 0.349 + x[1] * 0.686 + x[2] * 0.168)),
                int(min(255, x[0] * 0.272 + x[1] * 0.534 + x[2] * 0.131))
            )
            img = img.convert('RGB')
            pixels = img.load()
            width, height = img.size
            for x in range(width):
                for y in range(height):
                    pixels[x, y] = sepia_filter(pixels[x, y])
        
        elif filter_type == 'contrast':
            contrast_value = filter_settings.get('value', 1.5)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast_value)
        
        elif filter_type == 'brightness':
            brightness_value = filter_settings.get('value', 1.2)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness_value)
        
        elif filter_type == 'blur':
            blur_radius = filter_settings.get('radius', 2)
            img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        
        elif filter_type == 'sharpen':
            img = img.filter(ImageFilter.SHARPEN)
        
        elif filter_type == 'vintage':
            # Apply a combination of effects for vintage look
            # First, slightly desaturate
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(0.8)
            
            # Add slight sepia tone
            sepia_filter = lambda x: tuple(
                int(min(255, x[0] * 0.393 + x[1] * 0.769 + x[2] * 0.189)),
                int(min(255, x[0] * 0.349 + x[1] * 0.686 + x[2] * 0.168)),
                int(min(255, x[0] * 0.272 + x[1] * 0.534 + x[2] * 0.131))
            )
            img = img.convert('RGB')
            pixels = img.load()
            width, height = img.size
            for x in range(width):
                for y in range(height):
                    r, g, b = pixels[x, y]
                    pixels[x, y] = (
                        min(255, int(r * 0.9)),
                        min(255, int(g * 0.9)),
                        min(255, int(b * 0.7))
                    )
            
            # Add vignette effect
            img = add_vignette(img)
        
        # Save the modified image to a bytes buffer
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        
        return buffer.read()
    
    except Exception as e:
        print(f"Error applying filter: {str(e)}")
        return None

def add_vignette(img, level=0.3):
    """Add vignette effect to image"""
    width, height = img.size
    img = img.convert('RGB')
    
    # Create a radial gradient mask
    mask = PILImage.new('L', (width, height), 255)
    draw = PILImage.Draw(mask)
    
    radius = min(width, height) // 2
    center_x, center_y = width // 2, height // 2
    
    for y in range(height):
        for x in range(width):
            # Calculate distance from center
            distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
            # Normalize distance to [0, 1]
            norm_distance = min(1.0, distance / radius)
            
            # Darker at the edges
            level_adjusted = max(0, 255 - int(255 * norm_distance * level))
            mask.putpixel((x, y), level_adjusted)
    
    # Apply the mask
    return PILImage.composite(img, PILImage.new('RGB', img.size, (0, 0, 0)), mask)

@celery_app.task(name='process_image')
def process_image(filtered_image_id):
    """Process a single image with the specified filter"""
    with app.app_context():
        try:
            # Get filtered image record
            filtered_image = FilteredImage.query.get(uuid.UUID(filtered_image_id))
            if not filtered_image:
                print(f"Filtered image {filtered_image_id} not found")
                return False
            
            # Update status to processing
            filtered_image.status = ProcessingStatus.PROCESSING
            db.session.commit()
            
            # Get original image and filter
            original_image = Image.query.get(filtered_image.image_id)
            filter_obj = Filter.query.get(filtered_image.filter_id)
            
            if not original_image or not filter_obj:
                print(f"Original image or filter not found for {filtered_image_id}")
                filtered_image.status = ProcessingStatus.FAILED
                db.session.commit()
                return False
            
            # Download original image from storage
            image_data = download_from_s3(original_image.original_url)
            if not image_data:
                print(f"Failed to download image from {original_image.original_url}")
                filtered_image.status = ProcessingStatus.FAILED
                db.session.commit()
                return False
            
            # Process the image with filter
            processed_data = apply_filter(image_data, filter_obj.settings)
            if not processed_data:
                print(f"Failed to apply filter to image {filtered_image_id}")
                filtered_image.status = ProcessingStatus.FAILED
                db.session.commit()
                return False
            
            # Upload processed image to storage
            result_filename = f"filtered_{uuid.uuid4()}.jpg"
            result_url = upload_to_s3(processed_data, result_filename)
            
            if not result_url:
                print(f"Failed to upload processed image {filtered_image_id}")
                filtered_image.status = ProcessingStatus.FAILED
                db.session.commit()
                return False
            
            # Update filtered image record
            filtered_image.result_url = result_url
            filtered_image.status = ProcessingStatus.COMPLETED
            
            # Update job completion count
            if filtered_image.filter_job_id:
                job = FilterJob.query.get(filtered_image.filter_job_id)
                if job:
                    job.completed_count += 1
                    if job.completed_count >= job.image_count:
                        job.status = ProcessingStatus.COMPLETED
            
            db.session.commit()
            return True
        
        except Exception as e:
            print(f"Error in process_image task: {str(e)}")
            try:
                # Update status to failed
                filtered_image = FilteredImage.query.get(uuid.UUID(filtered_image_id))
                if filtered_image:
                    filtered_image.status = ProcessingStatus.FAILED
                    db.session.commit()
            except:
                pass
            return False

@celery_app.task(name='process_job')
def process_job(job_id):
    """Process all images in a filter job"""
    with app.app_context():
        try:
            # Get job record
            job = FilterJob.query.get(uuid.UUID(job_id))
            if not job:
                print(f"Job {job_id} not found")
                return False
            
            # Update job status
            job.status = ProcessingStatus.PROCESSING
            db.session.commit()
            
            # Get all filtered images for this job
            filtered_images = FilteredImage.query.filter_by(filter_job_id=job.id).all()
            
            # Queue each image for processing
            for img in filtered_images:
                process_image.delay(str(img.id))
            
            return True
        
        except Exception as e:
            print(f"Error in process_job task: {str(e)}")
            try:
                # Update status to failed
                job = FilterJob.query.get(uuid.UUID(job_id))
                if job:
                    job.status = ProcessingStatus.FAILED
                    db.session.commit()
            except:
                pass
            return False
