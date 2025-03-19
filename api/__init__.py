from flask import Blueprint


# Initialize Blueprint for the API
api_bp = Blueprint('api', __name__)

# Import routes from routes.py to register them with this Blueprint
from .routes import *
