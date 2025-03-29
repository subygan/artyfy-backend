import os
import json
import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if Firebase credentials are provided as environment variables
if os.getenv('FIREBASE_TYPE'):
    # Create credentials dictionary from environment variables
    cred_dict = {
        "type": os.getenv('FIREBASE_TYPE'),
        "project_id": os.getenv('FIREBASE_PROJECT_ID'),
        "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
        "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
        "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
        "client_id": os.getenv('FIREBASE_CLIENT_ID'),
        "auth_uri": os.getenv('FIREBASE_AUTH_URI'),
        "token_uri": os.getenv('FIREBASE_TOKEN_URI'),
        "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_X509_CERT_URL'),
        "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL'),
        "universe_domain": os.getenv('FIREBASE_UNIVERSE_DOMAIN', 'googleapis.com')
    }
    
    # Initialize Firebase app with credentials from environment variables
    cred = credentials.Certificate(cred_dict)
else:
    # Look for service account file
    service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', './firebase-service-account.json')
    
    # Check if service account file exists
    if os.path.exists(service_account_path):
        cred = credentials.Certificate(service_account_path)
    else:
        raise Exception(
            "Firebase credentials not found. Please provide either environment variables "
            "or a service account JSON file at " + service_account_path
        )

# Initialize the Firebase app
firebase_app = firebase_admin.initialize_app(cred)
