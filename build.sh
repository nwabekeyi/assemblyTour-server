#!/bin/bash

# Install dependencies
pip install -r requirements.txt


python manage.py clean_sqlite

# Run migrations
python manage.py migrate

# Create superuser from env variables
python create_super_admin.py

 python user_seed.py

# Collect static files
python manage.py collectstatic --noinput
