#!/bin/bash
set -e

echo "📦 Updating requirements.txt..."
pip freeze > requirements.txt

echo "📂 Staging files..."
git add .

echo "📝 Enter commit message:"
read commit_message

git commit -m "$commit_message"

echo "🚀 Pushing to GitHub..."
git push origin main

echo "✅ Deployment triggered!"
echo "ℹ️ Render will now install requirements, migrate DB, and collect static files."
