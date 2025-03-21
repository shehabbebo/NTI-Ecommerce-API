from flask import request, jsonify
from .. import api_bp
from models import Order, db, OrderItem, Product
from .shared_functions import process_image, delete_image
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone

@api_bp.route('/place_order', methods=['POST'])
@jwt_required()
def place_order():
    user_id = get_jwt_identity()  # Get the authenticated user ID
    
    data = request.get_json()
    if not data or "items" not in data:
        return jsonify({"status": False, "message": "Invalid order data"}), 400

    items = data["items"]  # Expecting a list of { "product_id": int, "quantity": int }
    if not isinstance(items, list) or len(items) == 0:
        return jsonify({"status": False, "message": "No items in order"}), 400

    subtotal = 0
    order_items = []

    for item in items:
        product = Product.query.get(item.get("product_id"))
        if not product:
            return jsonify({"status": False, "message": f"Product ID {item.get('product_id')} not found"}), 404
        
        quantity = item.get("quantity", 1)
        if quantity <= 0:
            return jsonify({"status": False, "message": f"Invalid quantity for product {product.name}"}), 400
        
        item_total = product.price * quantity
        subtotal += item_total

        order_items.append(OrderItem(
            product_id=product.id,
            quantity=quantity,
            current_unit_price=product.price
        ))

    # Example tax & shipping calculation (can be customized)
    tax = 0  
    shipping = 0
    total = subtotal + tax + shipping

    # Create the order
    new_order = Order(
        user_id=user_id,
        status=0,
        order_change_date=None,
        subtotal=subtotal,
        tax=tax,
        shipping=shipping,
        total=total
    )

    db.session.add(new_order)
    db.session.flush()  # Ensure order gets an ID before adding items

    # Assign the correct order_id to each order item and save them
    for order_item in order_items:
        order_item.order_id = new_order.id
        db.session.add(order_item)

    db.session.commit()

    return jsonify({
        "status": True,
        "message": "Order placed successfully",
        "order_id": new_order.id,
        "total": total
    }), 201
    
    
    
@api_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_user_orders():
    user_id = get_jwt_identity()  # Get logged-in user ID

    # Fetch orders categorized by status
    orders = Order.query.filter_by(user_id=user_id).all()
    if not orders:
        return jsonify({"status": False, "message": "No orders found"}), 404

    def format_order(order):
        """Helper function to format order data."""
        return {
            "id": order.id,
            "status": order.status,
            "order_date": order.order_date,
            "order_change_date": order.order_change_date,
            "subtotal": order.subtotal,
            "tax": order.tax,
            "shipping": order.shipping,
            "total": order.total,
            "driver": {
                "name": "Wael Mohamed",
                "phone": "01008965412",
                "longitude": 30.5878153960647, 
                "latitude": 31.479659660063422
            },
            "items": [
                {
                    "id": item.product.id,
                    "name": item.product.name,
                    "description": item.product.description,
                    "image_path": item.product.image_path,
                    "rating": item.product.rating,
                    "price": item.current_unit_price,
                    "quantity": item.quantity,
                    "total_price": item.quantity * item.current_unit_price
                }
                for item in order.order_items
            ]
        }

    # Categorize orders
    active_orders = [format_order(order) for order in orders if order.status == 0]
    completed_orders = [format_order(order) for order in orders if order.status == 1]
    canceled_orders = [format_order(order) for order in orders if order.status == 2]

    return jsonify({
        "status": True,
        "orders": {
            "active": active_orders,
            "completed": completed_orders,
            "canceled": canceled_orders
        }
    }), 200

@api_bp.route('/orders/cancel/<int:order_id>', methods=['POST'])
@jwt_required()
def cancel_order(order_id):
    user_id = get_jwt_identity()
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()

    if not order:
        return jsonify({"status": False, "message": "Order not found"}), 404

    if order.status == 2:
        return jsonify({"status": False, "message": "Order is already canceled"}), 400

    if order.status == 1:
        return jsonify({"status": False, "message": "Completed orders cannot be canceled"}), 400

    order.status = 2  # Set status to canceled
    order.order_change_date = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        "status": True,
        "message": "Order canceled successfully"
    }), 200

@api_bp.route('/orders/complete/<int:order_id>', methods=['POST'])
@jwt_required()
def complete_order(order_id):
    user_id = get_jwt_identity()
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()

    if not order:
        return jsonify({"status": False, "message": "Order not found"}), 404

    if order.status == 1:
        return jsonify({"status": False, "message": "Order is already completed"}), 400

    if order.status == 2:
        return jsonify({"status": False, "message": "Canceled orders cannot be completed"}), 400

    order.status = 1  # Set status to completed
    order.order_change_date = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        "status": True,
        "message": "Order completed successfully"
    }), 200
