from flask import Flask, jsonify, request, g
from flask_cors import CORS
import os
from dotenv import load_dotenv
from auth import auth_routes, token_required
from models import db, User, Filter, Image, FilteredImage, FilterJob, ProcessingStatus
import uuid
import json
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Set secret key for the app
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS', False)

# Initialize database
db.init_app(app)

# Register authentication routes
app.register_blueprint(auth_routes)

@app.route('/')
def hello():
    return jsonify({"message": "Artyfy API is running"})

@app.route('/protected', methods=['GET'])
@token_required
def protected_route():
    """Example of a protected route that requires authentication"""
    return jsonify({"message": "This is a protected route", "user_id": request.user_id})

# User-related routes
@app.route('/api/users/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current user's profile"""
    user = User.query.filter_by(firebase_uid=request.user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "id": str(user.id),
        "firebase_uid": user.firebase_uid,
        "email": user.email,
        "name": user.name,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat()
    })

# Filter-related routes
@app.route('/api/filters', methods=['GET'])
@token_required
def get_filters():
    """Get all filters for the user, including public and default filters"""
    user = User.query.filter_by(firebase_uid=request.user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Get user's filters and public/default filters
    filters = Filter.query.filter(
        (Filter.user_id == user.id) | 
        (Filter.is_public == True) | 
        (Filter.is_default == True)
    ).all()
    
    result = []
    for f in filters:
        result.append({
            "id": str(f.id),
            "user_id": str(f.user_id) if f.user_id else None,
            "name": f.name,
            "description": f.description,
            "settings": f.settings,
            "is_default": f.is_default,
            "is_public": f.is_public,
            "example_image_url": f.example_image_url,
            "popularity": f.popularity,
            "created_at": f.created_at.isoformat(),
            "updated_at": f.updated_at.isoformat()
        })
    
    return jsonify(result)

@app.route('/api/filters', methods=['POST'])
@token_required
def create_filter():
    """Create a new filter"""
    user = User.query.filter_by(firebase_uid=request.user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request data"}), 400
    
    # Validate required fields
    required_fields = ['name', 'settings']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Create new filter
    try:
        new_filter = Filter(
            user_id=user.id,
            name=data['name'],
            description=data.get('description'),
            settings=data['settings'],
            is_public=data.get('is_public', False),
            example_image_url=data.get('example_image_url')
        )
        db.session.add(new_filter)
        db.session.commit()
        
        return jsonify({
            "id": str(new_filter.id),
            "user_id": str(new_filter.user_id),
            "name": new_filter.name,
            "description": new_filter.description,
            "settings": new_filter.settings,
            "is_default": new_filter.is_default,
            "is_public": new_filter.is_public,
            "example_image_url": new_filter.example_image_url,
            "popularity": new_filter.popularity,
            "created_at": new_filter.created_at.isoformat(),
            "updated_at": new_filter.updated_at.isoformat()
        }), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/filters/<filter_id>', methods=['GET'])
@token_required
def get_filter(filter_id):
    """Get a specific filter by ID"""
    user = User.query.filter_by(firebase_uid=request.user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Find the filter
    try:
        filter_uuid = uuid.UUID(filter_id)
        filter_obj = Filter.query.filter(
            (Filter.id == filter_uuid) & 
            ((Filter.user_id == user.id) | (Filter.is_public == True) | (Filter.is_default == True))
        ).first()
        
        if not filter_obj:
            return jsonify({"error": "Filter not found or not accessible"}), 404
        
        return jsonify({
            "id": str(filter_obj.id),
            "user_id": str(filter_obj.user_id) if filter_obj.user_id else None,
            "name": filter_obj.name,
            "description": filter_obj.description,
            "settings": filter_obj.settings,
            "is_default": filter_obj.is_default,
            "is_public": filter_obj.is_public,
            "example_image_url": filter_obj.example_image_url,
            "popularity": filter_obj.popularity,
            "created_at": filter_obj.created_at.isoformat(),
            "updated_at": filter_obj.updated_at.isoformat()
        })
    except ValueError:
        return jsonify({"error": "Invalid filter ID format"}), 400
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/filters/<filter_id>', methods=['PUT'])
@token_required
def update_filter(filter_id):
    """Update a filter"""
    user = User.query.filter_by(firebase_uid=request.user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request data"}), 400
    
    # Find and update the filter
    try:
        filter_uuid = uuid.UUID(filter_id)
        filter_obj = Filter.query.filter_by(id=filter_uuid, user_id=user.id).first()
        
        if not filter_obj:
            return jsonify({"error": "Filter not found or not owned by user"}), 404
        
        # Update fields
        if 'name' in data:
            filter_obj.name = data['name']
        if 'description' in data:
            filter_obj.description = data['description']
        if 'settings' in data:
            filter_obj.settings = data['settings']
        if 'is_public' in data:
            filter_obj.is_public = data['is_public']
        if 'example_image_url' in data:
            filter_obj.example_image_url = data['example_image_url']
        
        db.session.commit()
        
        return jsonify({
            "id": str(filter_obj.id),
            "user_id": str(filter_obj.user_id),
            "name": filter_obj.name,
            "description": filter_obj.description,
            "settings": filter_obj.settings,
            "is_default": filter_obj.is_default,
            "is_public": filter_obj.is_public,
            "example_image_url": filter_obj.example_image_url,
            "popularity": filter_obj.popularity,
            "created_at": filter_obj.created_at.isoformat(),
            "updated_at": filter_obj.updated_at.isoformat()
        })
    except ValueError:
        return jsonify({"error": "Invalid filter ID format"}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/filters/<filter_id>', methods=['DELETE'])
@token_required
def delete_filter(filter_id):
    """Delete a filter"""
    user = User.query.filter_by(firebase_uid=request.user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Find and delete the filter
    try:
        filter_uuid = uuid.UUID(filter_id)
        filter_obj = Filter.query.filter_by(id=filter_uuid, user_id=user.id).first()
        
        if not filter_obj:
            return jsonify({"error": "Filter not found or not owned by user"}), 404
        
        db.session.delete(filter_obj)
        db.session.commit()
        
        return jsonify({"message": "Filter deleted successfully"})
    except ValueError:
        return jsonify({"error": "Invalid filter ID format"}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Image and processing-related routes
@app.route('/api/images', methods=['POST'])
@token_required
def upload_image():
    """Upload a new image"""
    # Note: Actual file upload will be handled by a storage service
    # This endpoint just creates the database record
    user = User.query.filter_by(firebase_uid=request.user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    if not data or 'original_url' not in data:
        return jsonify({"error": "Missing required field: original_url"}), 400
    
    try:
        new_image = Image(
            user_id=user.id,
            original_url=data['original_url']
        )
        db.session.add(new_image)
        db.session.commit()
        
        return jsonify({
            "id": str(new_image.id),
            "user_id": str(new_image.user_id),
            "original_url": new_image.original_url,
            "created_at": new_image.created_at.isoformat(),
            "updated_at": new_image.updated_at.isoformat()
        }), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/images', methods=['GET'])
@token_required
def get_user_images():
    """Get all images for the current user"""
    user = User.query.filter_by(firebase_uid=request.user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    images = Image.query.filter_by(user_id=user.id).all()
    result = []
    
    for img in images:
        result.append({
            "id": str(img.id),
            "user_id": str(img.user_id),
            "original_url": img.original_url,
            "created_at": img.created_at.isoformat(),
            "updated_at": img.updated_at.isoformat()
        })
    
    return jsonify(result)

@app.route('/api/process', methods=['POST'])
@token_required
def process_images():
    """Create a filter job to process images with a filter"""
    user = User.query.filter_by(firebase_uid=request.user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request data"}), 400
    
    # Validate required fields
    required_fields = ['filter_id', 'image_ids']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    try:
        # Verify filter exists and is accessible to the user
        filter_uuid = uuid.UUID(data['filter_id'])
        filter_obj = Filter.query.filter(
            (Filter.id == filter_uuid) & 
            ((Filter.user_id == user.id) | (Filter.is_public == True) | (Filter.is_default == True))
        ).first()
        
        if not filter_obj:
            return jsonify({"error": "Filter not found or not accessible"}), 404
        
        # Verify all images exist and belong to the user
        image_ids = [uuid.UUID(img_id) for img_id in data['image_ids']]
        images = Image.query.filter(Image.id.in_(image_ids), Image.user_id == user.id).all()
        
        if len(images) != len(image_ids):
            return jsonify({"error": "Some images not found or not owned by user"}), 404
        
        # Create filter job
        new_job = FilterJob(
            user_id=user.id,
            filter_id=filter_uuid,
            status=ProcessingStatus.PENDING,
            image_count=len(images),
            completed_count=0
        )
        db.session.add(new_job)
        
        # Create filtered image entries for each image
        for img in images:
            filtered_img = FilteredImage(
                image_id=img.id,
                filter_id=filter_uuid,
                filter_job_id=new_job.id,
                status=ProcessingStatus.PENDING
            )
            db.session.add(filtered_img)
        
        db.session.commit()
        
        # TODO: Queue the job for async processing with Celery
        # This will be implemented in a separate file
        
        return jsonify({
            "job_id": str(new_job.id),
            "user_id": str(new_job.user_id),
            "filter_id": str(new_job.filter_id),
            "status": new_job.status.value,
            "image_count": new_job.image_count,
            "completed_count": new_job.completed_count,
            "created_at": new_job.created_at.isoformat(),
            "updated_at": new_job.updated_at.isoformat()
        }), 201
    except ValueError:
        return jsonify({"error": "Invalid UUID format"}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs', methods=['GET'])
@token_required
def get_user_jobs():
    """Get all filter jobs for the current user"""
    user = User.query.filter_by(firebase_uid=request.user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    jobs = FilterJob.query.filter_by(user_id=user.id).all()
    result = []
    
    for job in jobs:
        result.append({
            "id": str(job.id),
            "user_id": str(job.user_id),
            "filter_id": str(job.filter_id),
            "status": job.status.value,
            "image_count": job.image_count,
            "completed_count": job.completed_count,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat()
        })
    
    return jsonify(result)

@app.route('/api/jobs/<job_id>', methods=['GET'])
@token_required
def get_job_details(job_id):
    """Get details of a specific filter job"""
    user = User.query.filter_by(firebase_uid=request.user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    try:
        job_uuid = uuid.UUID(job_id)
        job = FilterJob.query.filter_by(id=job_uuid, user_id=user.id).first()
        
        if not job:
            return jsonify({"error": "Job not found or not owned by user"}), 404
        
        # Get all filtered images for this job
        filtered_images = FilteredImage.query.filter_by(filter_job_id=job.id).all()
        images_data = []
        
        for img in filtered_images:
            original_image = Image.query.get(img.image_id)
            images_data.append({
                "id": str(img.id),
                "original_url": original_image.original_url if original_image else None,
                "result_url": img.result_url,
                "status": img.status.value
            })
        
        return jsonify({
            "id": str(job.id),
            "user_id": str(job.user_id),
            "filter_id": str(job.filter_id),
            "status": job.status.value,
            "image_count": job.image_count,
            "completed_count": job.completed_count,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "images": images_data
        })
    except ValueError:
        return jsonify({"error": "Invalid job ID format"}), 400
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500

# Application initialization
with app.app_context():
    # Create all tables in the database if they don't exist yet
    db.create_all()
    
    # Check if there are any default filters, if not create them
    default_filters_count = Filter.query.filter_by(is_default=True).count()
    if default_filters_count == 0:
        # Create default filters
        default_filters = [
            {
                "name": "Grayscale",
                "description": "Convert image to black and white",
                "settings": {"type": "grayscale"},
                "is_default": True,
                "is_public": True
            },
            {
                "name": "Sepia",
                "description": "Apply a warm brownish tone",
                "settings": {"type": "sepia"},
                "is_default": True,
                "is_public": True
            },
            {
                "name": "High Contrast",
                "description": "Increase image contrast",
                "settings": {"type": "contrast", "value": 1.5},
                "is_default": True,
                "is_public": True
            },
            {
                "name": "Vintage",
                "description": "Apply a vintage film look",
                "settings": {"type": "vintage"},
                "is_default": True,
                "is_public": True
            }
        ]
        
        for filter_data in default_filters:
            default_filter = Filter(**filter_data)
            db.session.add(default_filter)
        
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', True), host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
