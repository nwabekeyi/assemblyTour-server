#!/bin/bash
set -e

echo "🚀 Starting Assembly Tour Server..."

echo "📦 Installing dependencies..."
pip install --break-system-packages -r requirements.txt

echo "🗄️ Running migrations..."
python manage.py migrate --noinput

echo "👤 Creating superuser..."
python create_super_admin.py || true

echo "📝 Seeding registration steps..."
python registration_step_seed.py

echo "👤 Seeding test user..."
python user_seed.py || true

echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

echo "✅ All seeds completed. Starting gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT