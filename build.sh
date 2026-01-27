#!/bin/bash

# Run migrations
python manage.py migrate

python manage.py clean_sqlite


# Create superuser from env variables
python create_super_admin.py

# Collect static files
python manage.py collectstatic --noinput
