#!/bin/bash

echo "🔄 Adding changes..."
git add .

echo "📝 Enter commit message:"
read commit_message

git commit -m "$commit_message"

echo "🚀 Pushing to GitHub..."
git push origin main

echo "✅ Push complete!"
echo "ℹ️ Render will now run migrations and build automatically."
