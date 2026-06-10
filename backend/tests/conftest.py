import os

# Keep strict production config intact while making test collection self-contained.
os.environ.setdefault("JWT_SECRET", "pytest-jwt-secret-key-at-least-32-chars")
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "iems_test_db")
