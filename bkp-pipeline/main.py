# main.py - Entry point for App Engine
# This makes the app portable to any WSGI server

from app_engine_deployment import app

# This allows the app to run on:
# - Google App Engine
# - Heroku (with Procfile)
# - AWS Elastic Beanstalk
# - Any VPS with Gunicorn/uWSGI
# - Docker containers

if __name__ == '__main__':
    app.run()