from flask import Flask, jsonify
from api import api_bp
from config import Config
from models import db  
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config.from_object(Config)

jwt = JWTManager(app)
# Custom error handler for missing Authorization Header
@jwt.unauthorized_loader
def custom_missing_token_callback(error):
    return jsonify({"status": False, "message": "Token is missing. Please provide a valid token."}), 401

@jwt.expired_token_loader
def custom_expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        "status": False,
        "message": "Token has expired."
    }), 401


@jwt.invalid_token_loader
def custom_invalid_token_callback(error):
    # Custom error message for when only refresh tokens are allowed
    return jsonify({
        "status": False,
        "message": "Only refresh tokens are allowed. Please provide a valid refresh token."
    }), 422


db.init_app(app)
migrate = Migrate(app, db)

app.register_blueprint(api_bp, url_prefix='/api')

if __name__ == '__main__':
    app.run()
#host='0.0.0.0', port=5000
# gunicorn -w 4 -b 0.0.0.0:5000 app:app
