# Artyfy Backend

Artyfy is a mobile image editor that allows users to create and apply custom image filters. This backend API handles user authentication, filter management, and image processing.

## Features

- User authentication with Firebase
- Custom filter creation and management
- Asynchronous image processing with job queue
- Default and user-created filters
- Bulk image processing support
- RESTful API design

## Prerequisites

- Python 3.11 or higher
- PostgreSQL database
- Redis server (for Celery job queue)
- Firebase project for authentication
- S3-compatible storage for images

## Setup

### Firebase Setup

1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Enable Email/Password authentication in the Firebase Authentication section
3. Create a service account and download the credentials:
   - Go to Project Settings > Service Accounts
   - Click "Generate new private key"
   - Save this file as `firebase-service-account.json` in the project root, OR
   - Copy the environment variables from `.env.example` to a new `.env` file and fill in the values from the downloaded JSON

### Environment Variables

Copy the `.env.example` file to a new file named `.env` and fill in your Firebase credentials:

```
cp .env.example .env
```

Then edit the `.env` file with your actual Firebase service account details, database connection, and storage settings.

### Database Setup

1. Make sure PostgreSQL is installed and running
2. Create a database for the application
3. Update the DATABASE_URL in your `.env` file

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```
3. Install the dependencies:
   ```
   pip install -e .
   ```
4. Run the setup script to create database tables:
   ```
   python setup.py
   ```

## Running the Application

Start the main server:

```
python app.py
```

Start the Celery worker for background image processing:

```
celery -A tasks.celery_app worker --loglevel=info
```

The API will be available at `http://localhost:5000`.

## API Endpoints

### Authentication

- `POST /auth/register` - Register a new user
  - Body: `{ "email": "user@example.com", "password": "password123" }`
- `POST /auth/login` - Login simulation (actual auth done client-side with Firebase)
  - Body: `{ "email": "user@example.com" }`
- `POST /auth/verify-token` - Verify a Firebase token
  - Body: `{ "token": "your-firebase-token" }`
- `GET /auth/me` - Get current user information
  - Header: `Authorization: Bearer your-firebase-token`

### User Profile

- `GET /api/users/me` - Get current user profile
  - Header: `Authorization: Bearer your-firebase-token`

### Filters

- `GET /api/filters` - Get all filters (user's filters, public filters, and default filters)
  - Header: `Authorization: Bearer your-firebase-token`
- `POST /api/filters` - Create a new filter
  - Header: `Authorization: Bearer your-firebase-token`
  - Body: 
    ```json
    {
      "name": "My Filter",
      "description": "Custom filter with adjustments",
      "settings": {
        "type": "contrast",
        "value": 1.5
      },
      "is_public": false,
      "example_image_url": "https://example.com/image.jpg"
    }
    ```
- `GET /api/filters/{filter_id}` - Get a specific filter
  - Header: `Authorization: Bearer your-firebase-token`
- `PUT /api/filters/{filter_id}` - Update a filter
  - Header: `Authorization: Bearer your-firebase-token`
  - Body: (same format as POST but fields are optional)
- `DELETE /api/filters/{filter_id}` - Delete a filter
  - Header: `Authorization: Bearer your-firebase-token`

### Images

- `POST /api/images` - Register an uploaded image
  - Header: `Authorization: Bearer your-firebase-token`
  - Body: `{ "original_url": "https://your-storage.com/image.jpg" }`
- `GET /api/images` - Get all images for the current user
  - Header: `Authorization: Bearer your-firebase-token`

### Processing

- `POST /api/process` - Apply filter to images (creates a processing job)
  - Header: `Authorization: Bearer your-firebase-token`
  - Body: 
    ```json
    {
      "filter_id": "uuid-of-filter",
      "image_ids": ["uuid-of-image1", "uuid-of-image2"]
    }
    ```
- `GET /api/jobs` - Get all processing jobs for the current user
  - Header: `Authorization: Bearer your-firebase-token`
- `GET /api/jobs/{job_id}` - Get details of a specific job including processed images
  - Header: `Authorization: Bearer your-firebase-token`

## Filter Types

The application supports the following filter types:

1. **Grayscale** - Convert image to black and white
   ```json
   { "type": "grayscale" }
   ```

2. **Sepia** - Apply a warm brownish tone
   ```json
   { "type": "sepia" }
   ```

3. **Contrast** - Adjust image contrast
   ```json
   { "type": "contrast", "value": 1.5 }
   ```

4. **Brightness** - Adjust image brightness
   ```json
   { "type": "brightness", "value": 1.2 }
   ```

5. **Blur** - Apply Gaussian blur
   ```json
   { "type": "blur", "radius": 2 }
   ```

6. **Sharpen** - Enhance image details
   ```json
   { "type": "sharpen" }
   ```

7. **Vintage** - Apply vintage film effect
   ```json
   { "type": "vintage" }
   ```

## Authentication Flow

1. Client authenticates with Firebase Auth (using Firebase JS SDK)
2. Client receives ID token from Firebase
3. Client includes token in requests to backend as `Authorization: Bearer your-firebase-token`
4. Backend validates token and grants access to protected resources

## Development

For development, set `FLASK_ENV=development` and `FLASK_DEBUG=1` in your `.env` file.


# Set up the database
python setup.py

# Start the Flask API server
python app.py

# In a separate terminal, start the Celery worker
celery -A tasks.celery_app worker --loglevel=info