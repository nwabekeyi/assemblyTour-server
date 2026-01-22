import cloudinary.uploader
from django.core.management.base import BaseCommand
from homecontent.models import HeroSlide, ExperienceSection

class Command(BaseCommand):
    help = "Upload existing local media files to Cloudinary"

    def handle(self, *args, **kwargs):
        # Hero Slides
        for slide in HeroSlide.objects.all():
            if slide.image and not str(slide.image).startswith("http"):
                local_path = slide.image.path
                print(f"Uploading {local_path} to Cloudinary...")
                result = cloudinary.uploader.upload(
                    local_path,
                    folder="assemblytour/home/hero_slides"
                )
                slide.image = result['secure_url']
                slide.save()
                print(f"Updated slide {slide.id} to Cloudinary URL")

        # Experience Section (singleton)
        exp = ExperienceSection.objects.first()
        if exp:
            if exp.image_one and not str(exp.image_one).startswith("http"):
                local_path = exp.image_one.path
                print(f"Uploading {local_path} to Cloudinary...")
                result = cloudinary.uploader.upload(
                    local_path,
                    folder="home/experience"
                )
                exp.image_one = result['secure_url']

            if exp.image_two and not str(exp.image_two).startswith("http"):
                local_path = exp.image_two.path
                print(f"Uploading {local_path} to Cloudinary...")
                result = cloudinary.uploader.upload(
                    local_path,
                    folder="home/experience"
                )
                exp.image_two = result['secure_url']

            exp.save()
            print("Updated ExperienceSection to Cloudinary URLs")

        print("Migration to Cloudinary completed successfully!")
