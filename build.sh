#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser from env variables
python create_super_admin.py

# Collect static files
python manage.py collectstatic --noinput
