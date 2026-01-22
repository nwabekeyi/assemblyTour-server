from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile


def resize_image(image_field, max_width, max_height, quality=85):
    """
    Resize an image using Pillow before saving.
    Works with Django ImageField.
    """

    img = Image.open(image_field)

    # Convert to RGB (important for JPEG compatibility)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    img.thumbnail((max_width, max_height), Image.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)

    return ContentFile(buffer.read(), name=image_field.name)
