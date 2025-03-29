#!/usr/bin/env python3
import os
import subprocess
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_postgres():
    """Check if PostgreSQL is running and create the database if needed"""
    try:
        # Check database connection
        import psycopg2
        from urllib.parse import urlparse
        
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            print("ERROR: DATABASE_URL environment variable not set.")
            return False
        
        # Parse the database URL
        parsed_url = urlparse(db_url)
        dbname = parsed_url.path[1:]  # Remove leading slash
        user = parsed_url.username
        password = parsed_url.password
        host = parsed_url.hostname
        port = parsed_url.port or 5432
        
        # First try to connect to the PostgreSQL server without specifying a database
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database="postgres"  # Connect to default postgres database
        )
        conn.autocommit = True
        
        # Check if the database exists
        cursor = conn.cursor()
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{dbname}'")
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Creating database {dbname}...")
            cursor.execute(f"CREATE DATABASE {dbname}")
            print(f"Database {dbname} created successfully.")
        
        cursor.close()
        conn.close()
        
        # Now try to connect to the actual database
        conn = psycopg2.connect(db_url)
        conn.close()
        print("Database connection successful.")
        return True
        
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        return False

def run_migrations():
    """Run database migrations using Alembic"""
    try:
        # Make sure migrations/versions directory exists
        os.makedirs('migrations/versions', exist_ok=True)
        
        # Run Alembic migrations
        print("Running database migrations...")
        subprocess.run(["alembic", "revision", "--autogenerate", "-m", "Initial migration"], check=True)
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("Migrations completed successfully.")
        return True
    except Exception as e:
        print(f"Migration error: {str(e)}")
        return False

def main():
    """Main setup function"""
    print("Starting Artyfy backend setup...")
    
    # Check database connection
    if not check_postgres():
        print("ERROR: Could not connect to PostgreSQL database. Please check your settings.")
        sys.exit(1)
    
    # Run database migrations
    if not run_migrations():
        print("ERROR: Failed to run database migrations.")
        sys.exit(1)
    
    print("\nSetup completed successfully!")
    print("\nTo run the application server:")
    print("  python app.py")
    print("\nTo run the Celery worker for image processing:")
    print("  celery -A tasks.celery_app worker --loglevel=info")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
