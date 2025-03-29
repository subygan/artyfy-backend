from flask import Blueprint, request, jsonify
from functools import wraps
import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_config import firebase_app
from models import db, User
import uuid

auth_routes = Blueprint('auth', __name__, url_prefix='/auth')

def token_required(f):
    """Decorator to validate Firebase token for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in request headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            # Format should be "Bearer {token}"
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            # Verify the token with Firebase
            decoded_token = firebase_auth.verify_id_token(token, firebase_app)
            # Add user_id to request for use in protected routes
            request.user_id = decoded_token['uid']
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401
        
        return f(*args, **kwargs)
    
    return decorated

@auth_routes.route('/register', methods=['POST'])
def register():
    """Create a new user in Firebase Auth and in the database"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    
    try:
        # Create user in Firebase
        firebase_user = firebase_auth.create_user(
            email=email,
            password=password,
            display_name=name
        )
        
        # Check if user already exists in database
        existing_user = User.query.filter_by(firebase_uid=firebase_user.uid).first()
        if not existing_user:
            # Create user in database
            new_user = User(
                firebase_uid=firebase_user.uid,
                email=email,
                name=name or ""
            )
            db.session.add(new_user)
            db.session.commit()
        
        return jsonify({
            "message": "User created successfully",
            "user_id": firebase_user.uid,
            "email": email,
            "name": name
        }), 201
    except Exception as e:
        # Rollback database session if error
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@auth_routes.route('/login', methods=['POST'])
def login():
    """
    Login endpoint - Note: Actual authentication happens on client side with Firebase SDK
    This endpoint simply mimics a login response for testing purposes
    In a real implementation, the client would handle Firebase authentication and send token to backend
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    email = data.get('email')
    # In a real app we wouldn't process passwords server-side
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    # This is for illustration only - client should actually handle Firebase auth
    return jsonify({
        "message": "Please use Firebase client SDK to authenticate. This endpoint is for API testing only.",
        "email": email
    })

@auth_routes.route('/verify-token', methods=['POST'])
def verify_token():
    """Verify a Firebase token and return user info"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({"error": "Token is required"}), 400
    
    try:
        decoded_token = firebase_auth.verify_id_token(token, firebase_app)
        firebase_uid = decoded_token['uid']
        
        # Get Firebase user info
        firebase_user = firebase_auth.get_user(firebase_uid)
        
        # Check if user exists in database
        db_user = User.query.filter_by(firebase_uid=firebase_uid).first()
        if not db_user:
            # Create user in database if not exists
            new_user = User(
                firebase_uid=firebase_uid,
                email=firebase_user.email,
                name=firebase_user.display_name or ""
            )
            db.session.add(new_user)
            db.session.commit()
            db_user = new_user
        
        return jsonify({
            "user_id": firebase_uid,
            "email": firebase_user.email,
            "name": firebase_user.display_name,
            "email_verified": firebase_user.email_verified,
            "db_user_id": str(db_user.id)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 401

@auth_routes.route('/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current user information (protected route)"""
    try:
        firebase_user = firebase_auth.get_user(request.user_id)
        db_user = User.query.filter_by(firebase_uid=request.user_id).first()
        
        if not db_user:
            # Create user in database if not exists
            db_user = User(
                firebase_uid=request.user_id,
                email=firebase_user.email,
                name=firebase_user.display_name or ""
            )
            db.session.add(db_user)
            db.session.commit()
        
        # Combine Firebase and database user info
        return jsonify({
            "firebase_uid": firebase_user.uid,
            "db_user_id": str(db_user.id),
            "email": firebase_user.email,
            "name": firebase_user.display_name or db_user.name,
            "email_verified": firebase_user.email_verified,
            "created_at": db_user.created_at.isoformat() if db_user.created_at else None
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400
