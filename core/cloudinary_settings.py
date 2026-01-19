import os
import cloudinary

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# File restrictions
CLOUDINARY_ALLOWED_FILE_TYPES = ['jpg', 'jpeg', 'png', 'pdf']
CLOUDINARY_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Initialize Cloudinary globally
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)
