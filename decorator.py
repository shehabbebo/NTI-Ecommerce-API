from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from models import User

def check_blocked(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        # Check if the user is blocked
        if current_user and current_user.blocked:
            return jsonify({"status": False, "message": "Your account is blocked. You cannot perform any actions."}), 403
        
        return func(*args, **kwargs)
    return wrapper
