#!/bin/bash

echo "🚀 Starting Assembly Tour Server..."

echo "📦 Installing dependencies..."
pip install --break-system-packages -r requirements.txt

# Wait for database to be ready
wait_for_database() {
  echo "⏳ Waiting for database to be ready..."
  while ! python -c "import os; import django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); django.setup(); from django.db import connections; conn = connections['default']; conn.cursor()" 2>/dev/null; do
    echo "🔄 Database is unavailable - sleeping"
    sleep 1
  done
}

wait_for_database

echo "🗄️ Running migrations..."
python manage.py migrate --noinput

echo "👤 Creating superuser..."
python create_super_admin.py

echo "📝 Seeding registration steps..."
python registration_step_seed.py || true

echo "👤 Seeding test user..."
python user_seed.py || true

echo "📁 Collecting static files..."
python manage.py collectstatic --noinput || true

echo "✅ All seeds completed. Starting gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT