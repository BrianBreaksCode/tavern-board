#!/bin/sh
set -e
FLASK_APP=app.main flask seed-categories
exec gunicorn --bind 0.0.0.0:8000 --workers 2 app.main:app
