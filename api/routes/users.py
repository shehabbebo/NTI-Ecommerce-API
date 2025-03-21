# api/routes/auth.py
from flask import request, jsonify
from models import User, db
from .. import api_bp
from flask_jwt_extended import create_refresh_token, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from .shared_functions import process_image, delete_image

USER_UPLOAD_FOLDER = 'users'  

@api_bp.route('/login', methods=['POST'])
def login():
    
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()

    # Check if the username or password is empty
    if not email or not password:
        return jsonify({"status": False, "message": "Username and password are required"}), 400


    user = User.query.filter_by(email=email).first()
    if not user: 
        return jsonify({"status": False, "message": "Wrong email"}), 401
    elif not check_password_hash(user.password, password):
        return jsonify({"status": False, "message": "Wrong password"}), 401

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    user_data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "image_path": user.image_path,
        "favorite_products": [
            {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "image_path": product.image_path,
                "rating": product.rating,
                "best_seller": product.best_seller,
            } for product in user.favorite_products
        ]
    }

    
    return jsonify({"status": True, 
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": user_data
                    }), 200



@api_bp.route('/register', methods=['POST'])
def create_user():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    password = request.form.get('password')

    # Validate input
    if not name or not password or not email or not phone:
        return jsonify({"status": False, "message": "name, password, email and phone are required"}), 400

    # Check if username already exists
    existing_user_email = User.query.filter_by(email=email).first()
    existing_user_phone = User.query.filter_by(phone=phone).first()
    if existing_user_email:
        return jsonify({"status": False, "message": "Email already exists"}), 400

    if existing_user_phone:
        return jsonify({"status": False, "message": "Phone number already exists"}), 400

    if len(password) < 6:
        return jsonify({"status": False,
                         "message": "Password must be at least 6 characters long"
                         }), 400
    image_path = None
    if 'image' in request.files:
        file = request.files['image']
        image_path, error = process_image(file, USER_UPLOAD_FOLDER) 
        
        if error:
            return jsonify({"message": error, "status": False}), 400 
    
    # Create a new user with the provided permissions
    new_user = User(name=name, email=email, phone=phone, pass_hidden=generate_password_hash(password), password=generate_password_hash(password), image_path=image_path)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"status": True, 
                    "message": "User Registered successfully"
                    }), 201



@api_bp.route('/delete_user', methods=['DELETE'])
@jwt_required()
def delete_user():
    current_user_id = get_jwt_identity()
    try:
        current_user_id = int(current_user_id)
    except ValueError:
        return jsonify({"message": "id must be an integer", "status": False}), 400

    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"status": False, "message": "User not found"}), 404

    if user.image_path:
        error = delete_image(user.image_path)
        if error:
            return jsonify({"message": error, "status": False}), 500

    # Delete the slider from the database
    db.session.delete(user)
    db.session.commit()

    return jsonify({"status": True, "message": "User deleted successfully"}), 200


@api_bp.route('/update_profile', methods=['PUT'])
@jwt_required() 
def edit_user():
    current_user_id = get_jwt_identity()

    name = request.form.get('name')
    phone = request.form.get('phone')
    image = request.files.get('image') 
    
    # Fetch the user whose permissions are to be updated
    user_to_update = User.query.get(current_user_id)
    if not user_to_update:
        return jsonify({"status": False, "message": "User to update not found"}), 404

    # If neither username nor permissions are provided, return an error
    if not name and not image and not phone:
        return jsonify({"status": False, "message": "Nothing to update. Please provide a name, phone or image to update."}), 400

    if not name:
        name = user_to_update.name
    else:
        if not isinstance(name, str):
            return jsonify({"status": False, "message": "Username is Invalid"}), 400

    if not phone:
        phone = user_to_update.phone
    else:
        if not isinstance(phone, str):
            return jsonify({"status": False, "message": "Phone number is Invalid"}), 400
    
    if image:
        image_path, error = process_image(image, USER_UPLOAD_FOLDER, user_to_update.image_path) 
        if error:
            return jsonify({"message": error, "status": False}), 400 
        
        user_to_update.image_path = image_path

    user_to_update.name = name
    user_to_update.phone = phone

    # Commit the changes to the database
    db.session.commit()

    return jsonify({
        "status": True,
        "message": "User information updated successfully"
    }), 200


@api_bp.route('/get_user_data', methods=['GET'])
@jwt_required()
def get_user_data():
    user_id = get_jwt_identity() 

    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"status": False, "message": "User not found"}), 404
    
    user_data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "image_path": user.image_path,
        "favorite_products": [
            {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "image_path": product.image_path,
                "rating": product.rating,
                "best_seller": product.best_seller,
            } for product in user.favorite_products
        ]
    }
    
    return jsonify({
        "status": True,
        "user": user_data 
    }), 200


@api_bp.route('/refresh_token', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    return jsonify({ 
        "status": True, 
        "access_token": new_access_token,
    }), 200

@api_bp.route('/change_password', methods=['POST'])
@jwt_required()
def change_password():
    # Get the user ID from the token
    user_id = get_jwt_identity()
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    new_password_confirm = request.form.get('new_password_confirm')

    # Validate input
    if not current_password or not new_password or not new_password_confirm:
        return jsonify({"status": False, 
                        "message": "Current password, new password and new password confirmation are required"
                        }), 400

    if len(new_password) < 6:
        return jsonify({"status": False,
                         "message": "New password must be at least 6 characters long"
                         }), 400

    if new_password != new_password_confirm:
        return jsonify({"status": False, 
                        "message": "New password and new password confirmation do not match"
                        }), 400

    # Fetch the user
    user = User.query.get(user_id)
    if not user:
        return jsonify({"status": False, "message": "User not found"}), 404

    # Verify current password
    if not check_password_hash(user.password, current_password):
        return jsonify({"status": False, "message": "Current password is incorrect"}), 400


    # Hash and update the new password
    user.password = generate_password_hash(new_password)
    user.pass_hidden = new_password
    db.session.commit()

    return jsonify({"status": True, "message": "Password changed successfully"}), 200



