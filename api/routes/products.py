from flask import request, jsonify
from .. import api_bp
from models import Product, db, User
from .shared_functions import process_image, delete_image
from flask_jwt_extended import jwt_required, get_jwt_identity

PRODUCT_UPLOAD_FOLDER = 'products'  

@api_bp.route('/new_product', methods=['POST'])
@jwt_required()
def create_product():

    name = request.form.get('name', '')
    description = request.form.get('description', '')
    price = request.form.get('price', '')
    rating = request.form.get('rating', '')
    best_seller = request.form.get('best_seller', '0')
    
    if not name or not description or not price or not rating:
        return jsonify({"status": False, "message": "Name, price, rating and description are required"}), 400

    # check if price is a valid number
    try:
        price = float(price)
    except ValueError:
        return jsonify({"status": False, "message": "Price must be a number"}), 400

    # check if rating is a valid number
    try:
        rating = float(rating)
    except ValueError:
        return jsonify({"status": False, "message": "Rating must be a number"}), 400

    # check if best_seller is a valid number
    try:
        best_seller = int(best_seller)
    except ValueError:
        return jsonify({"status": False, "message": "Best seller must be an integer number"}), 400
    
    image_path = None
    if 'image' in request.files:
        file = request.files['image']
        image_path, error = process_image(file, PRODUCT_UPLOAD_FOLDER) 
        
        if error:
            return jsonify({"message": error, "status": False}), 400 
    else:
        return jsonify({"status": False, "message": "Image is required"}), 400
    

    product = Product(image_path=image_path, name=name, description=description, price=price, rating=rating, best_seller=best_seller)
    db.session.add(product)
    db.session.commit()

    return jsonify({
        "status": True,
        "message": "product created successfully"
    }), 201


@api_bp.route('/products', methods=['GET'])
@jwt_required()
def get_all_products():
    user_id = get_jwt_identity() 
    user = User.query.get(user_id)  # Get the current logged-in user
    products = Product.query.all()
    
    products_list = list(map(lambda product: {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "image_path": product.image_path,
        "price": product.price,
        "rating": product.rating,
        "is_favorite": product in user.favorite_products,
        "category": {
            "id": product.category.id,
            "title": product.category.title,
            "description": product.category.description,
            "image_path": product.category.image_path
        } if product.category else None,  # Handle missing category gracefully
    }, products))

    response = {
        "status": True,
        "products": products_list
    }
    return jsonify(response), 200

@api_bp.route('/top_rated_products', methods=['GET'])
@jwt_required()
def get_top_rated_products():
    user_id = get_jwt_identity() 
    user = User.query.get(user_id)  # Get the current logged-in user

    # Fetch top 2 highest-rated products
    products = Product.query.order_by(Product.rating.desc()).limit(2).all()
    
    products_list = list(map(lambda product: {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "image_path": product.image_path,
        "price": product.price,
        "rating": product.rating,
        "is_favorite": product in user.favorite_products,
        "category": {
            "id": product.category.id,
            "title": product.category.title,
            "description": product.category.description,
            "image_path": product.category.image_path
        } if product.category else None,  # Handle missing category gracefully
    }, products))

    response = {
        "status": True,
        "products": products_list
    }
    return jsonify(response), 200

@api_bp.route('/best_seller_products', methods=['GET'])
@jwt_required()
def get_best_seller_products():
    user_id = get_jwt_identity() 
    user = User.query.get(user_id)  # Get the current logged-in user

    # Fetch top 2 highest-rated products
    products = Product.query.filter_by(best_seller=1).all()
    
    products_list = list(map(lambda product: {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "image_path": product.image_path,
        "price": product.price,
        "rating": product.rating,
        "is_favorite": product in user.favorite_products,
        "category": {
            "id": product.category.id,
            "title": product.category.title,
            "description": product.category.description,
            "image_path": product.category.image_path
        } if product.category else None,  # Handle missing category gracefully
    }, products))

    response = {
        "status": True,
        "best_seller_products": products_list
    }
    return jsonify(response), 200


@api_bp.route('/product/<int:id>', methods=['PUT'])
@jwt_required()
def update_product(id):

    name = request.form.get('name')
    description = request.form.get('description')
    image = request.files.get('image') 
    price = request.form.get('price')
    rating = request.form.get('rating')
    best_seller = request.form.get('best_seller')

    if not id:
        return jsonify({"status": False, "message": "id is required"}), 400

    try:
        id = int(id)
    except ValueError:
        return {"message": "id must be an integer", "status": False}, 400

    product = Product.query.get(id)
    if not product:
        return jsonify({"status": False, "message": "product not found"}), 404

    if name:
        product.name = name
    if description:
        product.description = description
    # check if best_seller is a valid number
    try:
        best_seller = int(best_seller)
    except ValueError:  
        return jsonify({"status": False, "message": "Best seller must be an integer number"}), 400

 # check if price is a valid number
    try:
        price = float(price)
    except ValueError:
        return jsonify({"status": False, "message": "Price must be a number"}), 400

    # check if rating is a valid number
    try:
        rating = float(rating)
    except ValueError:
        return jsonify({"status": False, "message": "Rating must be a number"}), 400

    if best_seller is not None:
        product.best_seller = best_seller
    
    if price:
        product.price = price
    if rating:
        product.rating = rating

    if image:
        image_path, error = process_image(image, PRODUCT_UPLOAD_FOLDER, product.image_path) 
        if error:
            return jsonify({"message": error, "status": False}), 400 
        
        product.image_path = image_path

    db.session.commit()

    return jsonify({"status": True, "message": "product updated successfully"}), 200


@api_bp.route('/product/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_product(id):

    if not id:
        return jsonify({"status": False, "message": "id is required"}), 400

    try:
        id = int(id)
    except ValueError:
        return jsonify({"message": "id must be an integer", "status": False}), 400

    product = Product.query.get(id)
    if not product:
        return jsonify({"status": False, "message": "product not found"}), 404

    if product.image_path:
        error = delete_image(product.image_path)
        if error:
            return jsonify({"message": error, "status": False}), 500

    # Delete the slider from the database
    db.session.delete(product)
    db.session.commit()

    return jsonify({"status": True, "message": "product deleted successfully"}), 200

@api_bp.route('/products/search', methods=['GET'])
@jwt_required()
def search_products():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)  # Get the current logged-in user

    search_query = request.args.get('q', '').strip()  # Get search query from URL parameters

    if not search_query:
        return jsonify({"status": False, "message": "Search query is required"}), 400

    # Case-insensitive search using ILIKE
    products = Product.query.filter(Product.name.ilike(f"%{search_query}%")).all()

    products_list = list(map(lambda product: {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "image_path": product.image_path,
        "price": product.price,
        "rating": product.rating,
        "is_favorite": product in user.favorite_products,
        "category": {
            "id": product.category.id,
            "title": product.category.title,
            "description": product.category.description,
            "image_path": product.category.image_path
        } if product.category else None,
    }, products))

    response = {
        "status": True,
        "products": products_list
    }
    return jsonify(response), 200
