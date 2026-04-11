#!/usr/bin/env bash
# Build script for Render.com
# This runs automatically during each deployment

set -o errexit  # Exit on error

# Install Python dependencies
pip install -r requirements.txt

# Apply all database migrations (creates auth_user, core tables, etc.)
python manage.py migrate --no-input

# Collect static files for WhiteNoise to serve
python manage.py collectstatic --no-input
