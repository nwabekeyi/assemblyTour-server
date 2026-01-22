import os
import cloudinary
import cloudinary.uploader
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

class CloudinaryService:
    """
    Handles Cloudinary upload, delete, and image resizing.
    Always uploads under 'assemblytour' base folder.
    """
    BASE_FOLDER = "assemblytour"
    ALLOWED_FILE_TYPES = ["jpg", "jpeg", "png", "pdf"]

    def __init__(self):
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET")
        )

    def resize_image(self, file, max_width: int, max_height: int):
        """
        Resize image using Pillow before uploading
        """
        img = Image.open(file)
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)        
        buffer = BytesIO()
        img.save(buffer, format=img.format)
        return ContentFile(buffer.getvalue(), name=file.name)

    def upload(self, file, subfolder=""):
        """
        Upload file to Cloudinary under the 'assemblytour' folder
        """
        ext = file.name.split('.')[-1].lower()
        if ext not in self.ALLOWED_FILE_TYPES:
            raise ValueError(f"File type '{ext}' not allowed. Allowed: {self.ALLOWED_FILE_TYPES}")

        folder_path = f"{self.BASE_FOLDER}/{subfolder}" if subfolder else self.BASE_FOLDER
        return cloudinary.uploader.upload(file, folder=folder_path)

    def delete(self, public_id: str):
        """
        Delete file from Cloudinary
        """
        return cloudinary.uploader.destroy(public_id)
