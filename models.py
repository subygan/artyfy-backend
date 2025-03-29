from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy import Enum as SQLAlchemyEnum
import uuid
from datetime import datetime
import enum

db = SQLAlchemy()

class ProcessingStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = db.Column(db.String(128), unique=True, nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    filters = db.relationship('Filter', backref='user', lazy=True, cascade="all, delete-orphan")
    images = db.relationship('Image', backref='user', lazy=True, cascade="all, delete-orphan")
    filter_jobs = db.relationship('FilterJob', backref='user', lazy=True, cascade="all, delete-orphan")

class Filter(db.Model):
    __tablename__ = 'filters'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    settings = db.Column(JSON, nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean, default=False)
    popularity = db.Column(db.Integer, default=0)
    example_image_url = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    filtered_images = db.relationship('FilteredImage', backref='filter', lazy=True, cascade="all, delete-orphan")
    filter_jobs = db.relationship('FilterJob', backref='filter', lazy=True, cascade="all, delete-orphan")

class Image(db.Model):
    __tablename__ = 'images'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    original_url = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    filtered_images = db.relationship('FilteredImage', backref='image', lazy=True, cascade="all, delete-orphan")

class FilteredImage(db.Model):
    __tablename__ = 'filtered_images'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_id = db.Column(UUID(as_uuid=True), db.ForeignKey('images.id'), nullable=False)
    filter_id = db.Column(UUID(as_uuid=True), db.ForeignKey('filters.id'), nullable=False)
    result_url = db.Column(db.String(512), nullable=True)
    status = db.Column(SQLAlchemyEnum(ProcessingStatus), nullable=False, default=ProcessingStatus.PENDING)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    filter_job_id = db.Column(UUID(as_uuid=True), db.ForeignKey('filter_jobs.id'), nullable=True)

class FilterJob(db.Model):
    __tablename__ = 'filter_jobs'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    filter_id = db.Column(UUID(as_uuid=True), db.ForeignKey('filters.id'), nullable=False)
    status = db.Column(SQLAlchemyEnum(ProcessingStatus), nullable=False, default=ProcessingStatus.PENDING)
    image_count = db.Column(db.Integer, default=0)
    completed_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    filtered_images = db.relationship('FilteredImage', backref='filter_job', lazy=True)
