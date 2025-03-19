from flask import request, jsonify
from .. import api_bp
from models import Slider, db, User
from .shared_functions import process_image, delete_image
from flask_jwt_extended import jwt_required, get_jwt_identity

SLIDER_UPLOAD_FOLDER = 'sliders'  

@api_bp.route('/new_slider', methods=['POST'])
@jwt_required()
def create_slider():

    title = request.form.get('title', '')
    description = request.form.get('description', '')
    
    if not title or not description:
        return jsonify({"status": False, "message": "Title and description are required"}), 400

    image_path = None
    if 'image' in request.files:
        file = request.files['image']
        image_path, error = process_image(file, SLIDER_UPLOAD_FOLDER) 
        
        if error:
            return jsonify({"message": error, "status": False}), 400 
    else:
        return jsonify({"status": False, "message": "Image is required"}), 400
    

    slider = Slider(image_path=image_path, title=title, description=description)
    db.session.add(slider)
    db.session.commit()

    return jsonify({
        "status": True,
        "message": "Slider created successfully"
    }), 201


@api_bp.route('/sliders', methods=['GET'])
def get_all_sliders():
    sliders = Slider.query.all()
    
    slider_list = list(map(lambda slider: {
        "id": slider.id,
        "title": slider.title,
        "description": slider.description,
        "image_path": slider.image_path
    }, sliders))

    response = {
        "status": True,
        "sliders": slider_list
    }
    return jsonify(response), 200



@api_bp.route('/slider/<int:id>', methods=['GET'])
def get_slider(id):
    
    if not id:
        return {
            "message": "id is required as a query parameter",
            "status": False
            }, 400
    
    try:
        id = int(id)
    except ValueError:
        return {"message": "id must be an integer", "status": False}, 400

    
    slider = Slider.query.get(id)
    if not slider:
        return {
            "message": "Slider not found",
            "status": False
            }, 404
    
    response = {
        "status": True,
        "slider": {
            "id": slider.id,
            "title": slider.title,
            "description": slider.description,
            "image_path": slider.image_path,
        },
    }
    return jsonify(response), 200


@api_bp.route('/slider/<int:id>', methods=['PUT'])
@jwt_required()
def update_slider(id):

    title = request.form.get('title')
    description = request.form.get('description')
    image = request.files.get('image') 

    if not id:
        return jsonify({"status": False, "message": "id is required"}), 400

    try:
        id = int(id)
    except ValueError:
        return {"message": "id must be an integer", "status": False}, 400

    slider = Slider.query.get(id)
    if not slider:
        return jsonify({"status": False, "message": "Slider not found"}), 404

    if title:
        slider.title = title
    if description:
        slider.description = description

    if image:
        image_path, error = process_image(image, SLIDER_UPLOAD_FOLDER, slider.image_path) 
        if error:
            return jsonify({"message": error, "status": False}), 400 
        
        slider.image_path = image_path

    db.session.commit()

    return jsonify({"status": True, "message": "Slider updated successfully", "slider": {
        "id": slider.id,
        "title": slider.title,
        "description": slider.description,
        "image_path": slider.image_path
    }}), 200


@api_bp.route('/slider/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_slider(id):

    if not id:
        return jsonify({"status": False, "message": "id is required"}), 400

    try:
        id = int(id)
    except ValueError:
        return jsonify({"message": "id must be an integer", "status": False}), 400

    slider = Slider.query.get(id)
    if not slider:
        return jsonify({"status": False, "message": "Slider not found"}), 404

    if slider.image_path:
        error = delete_image(slider.image_path)
        if error:
            return jsonify({"message": error, "status": False}), 500

    # Delete the slider from the database
    db.session.delete(slider)
    db.session.commit()

    return jsonify({"status": True, "message": "Slider deleted successfully"}), 200

