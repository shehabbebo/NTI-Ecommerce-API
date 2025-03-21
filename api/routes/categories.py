from flask import request, jsonify
from .. import api_bp
from models import Category, db, User
from .shared_functions import process_image, delete_image
from flask_jwt_extended import jwt_required, get_jwt_identity

CATEGORY_UPLOAD_FOLDER = 'categories'  

@api_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_all_categories():
    user_id = get_jwt_identity() 
    user = User.query.get(user_id)  # Get the current logged-in user
    categories = Category.query.all()
    
    category_list = []
    for category in categories:
        category_list.append({
            "id": category.id,
            "title": category.title,
            "description": category.description,
            "image_path": category.image_path,
            "products": [
                {
                    "id": product.id,
                    "name": product.name,
                    "description": product.description,
                    "price": product.price,
                    "image_path": product.image_path,
                    "rating": product.rating,
                    "best_seller": product.best_seller,
                    "is_favorite": product in user.favorite_products,
                } for product in category.products  # Access related products
            ]
        })

    response = {
        "status": True,
        "categories": category_list
    }
    return jsonify(response), 200

@api_bp.route('/new_category', methods=['POST'])
@jwt_required()
def create_category():

    title = request.form.get('title', '')
    description = request.form.get('description', '')
    
    if not title or not description:
        return jsonify({"status": False, "message": "Title and description are required"}), 400

    image_path = None
    if 'image' in request.files:
        file = request.files['image']
        image_path, error = process_image(file, CATEGORY_UPLOAD_FOLDER) 
        
        if error:
            return jsonify({"message": error, "status": False}), 400 
    else:
        return jsonify({"status": False, "message": "Image is required"}), 400
    

    category = Category(image_path=image_path, title=title, description=description)
    db.session.add(category)
    db.session.commit()

    return jsonify({
        "status": True,
        "message": "Category created successfully"
    }), 201



@api_bp.route('/category/<int:id>', methods=['PUT'])
@jwt_required()
def update_category(id):

    title = request.form.get('title')
    description = request.form.get('description')
    image = request.files.get('image') 

    if not id:
        return jsonify({"status": False, "message": "id is required"}), 400

    try:
        id = int(id)
    except ValueError:
        return {"message": "id must be an integer", "status": False}, 400

    category = Category.query.get(id)
    if not category:
        return jsonify({"status": False, "message": "category not found"}), 404

    if title:
        category.title = title
    if description:
        category.description = description

    if image:
        image_path, error = process_image(image, CATEGORY_UPLOAD_FOLDER, category.image_path) 
        if error:
            return jsonify({"message": error, "status": False}), 400 
        
        category.image_path = image_path

    db.session.commit()

    return jsonify({"status": True, "message": "category updated successfully", "category": {
        "id": category.id,
        "title": category.title,
        "description": category.description,
        "image_path": category.image_path
    }}), 200


@api_bp.route('/category/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_category(id):

    if not id:
        return jsonify({"status": False, "message": "id is required"}), 400

    try:
        id = int(id)
    except ValueError:
        return jsonify({"message": "id must be an integer", "status": False}), 400

    category = Category.query.get(id)
    if not category:
        return jsonify({"status": False, "message": "category not found"}), 404

    if category.image_path:
        error = delete_image(category.image_path)
        if error:
            return jsonify({"message": error, "status": False}), 500

    db.session.delete(category)
    db.session.commit()

    return jsonify({"status": True, "message": "category deleted successfully"}), 200

