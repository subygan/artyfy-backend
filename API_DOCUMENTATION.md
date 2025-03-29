# Artyfy API Documentation

## Base URL
```
http://localhost:5000
```

## Authentication
Artyfy uses Firebase Authentication. Include a Firebase ID token in the Authorization header for protected routes:

```
Authorization: Bearer YOUR_FIREBASE_TOKEN
```

## Authentication Endpoints

### Register User
```
POST /auth/register
```

Register a new user in both Firebase and the Artyfy database.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "User Name"
}
```

**Response (201 Created):**
```json
{
  "message": "User created successfully",
  "user_id": "firebase-uid",
  "email": "user@example.com",
  "name": "User Name"
}
```

### Login
```
POST /auth/login
```

**Note:** This endpoint is for API testing only. In the actual implementation, authentication should be performed client-side using the Firebase SDK.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Please use Firebase client SDK to authenticate. This endpoint is for API testing only.",
  "email": "user@example.com"
}
```

### Verify Token
```
POST /auth/verify-token
```

Verify a Firebase token and return user information.

**Request Body:**
```json
{
  "token": "firebase-id-token"
}
```

**Response (200 OK):**
```json
{
  "user_id": "firebase-uid",
  "email": "user@example.com",
  "name": "User Name",
  "email_verified": true,
  "db_user_id": "database-user-id"
}
```

### Get Current User
```
GET /auth/me
```

Get current authenticated user's information.

**Headers:**
```
Authorization: Bearer YOUR_FIREBASE_TOKEN
```

**Response (200 OK):**
```json
{
  "firebase_uid": "firebase-uid",
  "db_user_id": "database-user-id",
  "email": "user@example.com",
  "name": "User Name",
  "email_verified": true,
  "created_at": "2023-01-01T00:00:00"
}
```

## User Endpoints

### Get Current User Profile
```
GET /api/users/me
```

Get current user's profile information.

**Headers:**
```
Authorization: Bearer YOUR_FIREBASE_TOKEN
```

**Response (200 OK):**
```json
{
  "id": "user-id",
  "firebase_uid": "firebase-uid",
  "email": "user@example.com",
  "name": "User Name",
  "created_at": "2023-01-01T00:00:00",
  "updated_at": "2023-01-01T00:00:00"
}
```

## Filter Endpoints

### Get All Filters
```
GET /api/filters
```

Get all filters accessible to the user (including user's own filters, public filters, and default filters).

**Headers:**
```
Authorization: Bearer YOUR_FIREBASE_TOKEN
```

**Response (200 OK):**
```json
[
  {
    "id": "filter-id",
    "user_id": "user-id",
    "name": "Filter Name",
    "description": "Filter Description",
    "settings": { "type": "filter_type", "params": {} },
    "is_default": false,
    "is_public": true,
    "example_image_url": "https://example.com/image.jpg",
    "popularity": 0,
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00"
  }
]
```

### Create Filter
```
POST /api/filters
```

Create a new custom filter.

**Headers:**
```
Authorization: Bearer YOUR_FIREBASE_TOKEN
```

**Request Body:**
```json
{
  "name": "My Custom Filter",
  "description": "A custom filter created by me",
  "settings": { "type": "custom", "params": {} },
  "is_public": false,
  "example_image_url": "https://example.com/example.jpg"
}
```

**Response (201 Created):**
```json
{
  "id": "filter-id",
  "user_id": "user-id",
  "name": "My Custom Filter",
  "description": "A custom filter created by me",
  "settings": { "type": "custom", "params": {} },
  "is_default": false,
  "is_public": false,
  "example_image_url": "https://example.com/example.jpg",
  "popularity": 0,
  "created_at": "2023-01-01T00:00:00",
  "updated_at": "2023-01-01T00:00:00"
}
```

### Get Filter by ID
```
GET /api/filters/{filter_id}
```

Get a specific filter by ID.

**Headers:**
```
Authorization: Bearer YOUR_FIREBASE_TOKEN
```

**Response (200 OK):**
```json
{
  "id": "filter-id",
  "user_id": "user-id",
  "name": "Filter Name",
  "description": "Filter Description",
  "settings": { "type": "filter_type", "params": {} },
  "is_default": false,
  "is_public": true,
  "example_image_url": "https://example.com/image.jpg",
  "popularity": 0,
  "created_at": "2023-01-01T00:00:00",
  "updated_at": "2023-01-01T00:00:00"
}
```

### Update Filter
```
PUT /api/filters/{filter_id}
```

Update an existing filter. You can only update filters that you own.

**Headers:**
```
Authorization: Bearer YOUR_FIREBASE_TOKEN
```

**Request Body:**
```json
{
  "name": "Updated Filter Name",
  "description": "Updated filter description",
  "settings": { "type": "updated_type", "params": {} },
  "is_public": true,
  "example_image_url": "https://example.com/updated.jpg"
}
```

**Response (200 OK):**
```json
{
  "id": "filter-id",
  "user_id": "user-id",
  "name": "Updated Filter Name",
  "description": "Updated filter description",
  "settings": { "type": "updated_type", "params": {} },
  "is_default": false,
  "is_public": true,
  "example_image_url": "https://example.com/updated.jpg",
  "popularity": 0,
  "created_at": "2023-01-01T00:00:00",
  "updated_at": "2023-01-01T00:00:00"
}
```

### Delete Filter
```
DELETE /api/filters/{filter_id}
```

Delete a filter. You can only delete filters that you own.

**Headers:**
```
Authorization: Bearer YOUR_FIREBASE_TOKEN
```

**Response (200 OK):**
```json
{
  "message": "Filter deleted successfully"
}
```

## Image Endpoints

### Upload Image
```
POST /api/images
```

Upload a new image record. Note: This endpoint only creates the database record, actual file upload is handled by a storage service.

**Headers:**
```
Authorization: Bearer YOUR_FIREBASE_TOKEN
```

**Request Body:**
```json
{
  "original_url": "https://storage.example.com/image.jpg"
}
```

**Response (201 Created):**
```json
{
  "id": "image-id",
  "user_id": "user-id",
  "original_url": "https://storage.example.com/image.jpg",
  "created_at": "2023-01-01T00:00:00",
  "updated_at": "2023-01-01T00:00:00"
}
```

### Get User Images
```
GET /api/images
```

Get all images uploaded by the current user.

**Headers:**
```
Authorization: Bearer YOUR_FIREBASE_TOKEN
```

**Response (200 OK):**
```json
[
  {
    "id": "image-id",
    "user_id": "user-id",
    "original_url": "https://storage.example.com/image.jpg",
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00"
  }
]
```

## Processing Endpoints

### Process Images with Filter
```
POST /api/process
```

Create a filter job to process one or more images with a selected filter.

**Headers:**
```
Authorization: Bearer YOUR_FIREBASE_TOKEN
```

**Request Body:**
```json
{
  "filter_id": "filter-id",
  "image_ids": ["image-id-1", "image-id-2"]
}
```

**Response (201 Created):**
```json
{
  "job_id": "job-id",
  "user_id": "user-id",
  "filter_id": "filter-id",
  "status": "pending",
  "image_count": 2,
  "completed_count": 0,
  "created_at": "2023-01-01T00:00:00",
  "updated_at": "2023-01-01T00:00:00"
}
```

### Get User Jobs
```
GET /api/jobs
```

Get all filter jobs created by the current user.

**Headers:**
```
Authorization: Bearer YOUR_FIREBASE_TOKEN
```

**Response (200 OK):**
```json
[
  {
    "id": "job-id",
    "user_id": "user-id",
    "filter_id": "filter-id",
    "status": "pending",
    "image_count": 2,
    "completed_count": 0,
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00"
  }
]
```

### Get Job Details
```
GET /api/jobs/{job_id}
```

Get detailed information about a specific filter job, including the processing status of each image.

**Headers:**
```
Authorization: Bearer YOUR_FIREBASE_TOKEN
```

**Response (200 OK):**
```json
{
  "id": "job-id",
  "user_id": "user-id",
  "filter_id": "filter-id",
  "status": "processing",
  "image_count": 2,
  "completed_count": 1,
  "created_at": "2023-01-01T00:00:00",
  "updated_at": "2023-01-01T00:00:00",
  "images": [
    {
      "id": "filtered-image-id",
      "original_url": "https://storage.example.com/original.jpg",
      "result_url": "https://storage.example.com/filtered.jpg",
      "status": "completed"
    },
    {
      "id": "filtered-image-id-2",
      "original_url": "https://storage.example.com/original2.jpg",
      "result_url": null,
      "status": "pending"
    }
  ]
}
```

## Error Responses

All endpoints may return the following error responses:

**401 Unauthorized:**
```json
{
  "message": "Token is missing!"
}
```
or
```json
{
  "message": "Token is invalid!",
  "error": "Error details"
}
```

**404 Not Found:**
```json
{
  "error": "Resource not found"
}
```

**400 Bad Request:**
```json
{
  "error": "Error message explaining the issue"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error details"
}
```
