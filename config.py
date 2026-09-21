"""
Configuration settings for the Student Result Management System.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Secret key used for session signing / CSRF. In production, set this
    # via an environment variable instead of hardcoding it.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'srms-dev-secret-key-change-me')

    # SQLite database stored alongside the project.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploaded student photos are stored here.
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'images', 'students')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max upload

    # Session cookie hardening.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    COLLEGE_NAME = "Sunrise Institute of Technology"
    COLLEGE_ADDRESS = "123 Knowledge Park, Bengaluru, Karnataka"
