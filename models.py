from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from sqlalchemy import UniqueConstraint

db = SQLAlchemy()

class Slider(db.Model):
    __tablename__ = 'sliders'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True) 
    image_path = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<Slider {self.title}>'
    
# Association Table for Many-to-Many (Users & Favorite Products)
favorites = db.Table(
    'favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True)
)
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=False, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    pass_hidden = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(255), nullable=True)
    
    # Relationship: User can have many favorite products
    favorite_products = db.relationship('Product', secondary=favorites, lazy='dynamic')

    # Relationship: User can place multiple orders
    orders = db.relationship('Order', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.name}>'
    
class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True) 
    image_path = db.Column(db.String(255), nullable=True)
    
    # Relationship: One Category -> Many Products
    products = db.relationship('Product', backref='category', lazy=True)


    def __repr__(self):
        return f'<Category {self.title}>'
    
    

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image_path = db.Column(db.String(255), nullable=True)
    rating = db.Column(db.Float, nullable=True)
    best_seller = db.Column(db.Integer, nullable=False, default=0)
    

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)


    def __repr__(self):
        return f"<Product {self.name}>"
    


# Order Model
class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.Integer, nullable=False, default=0)  # Example: active = 0, completed = 1, cancelled = 2
    order_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    order_change_date = db.Column(db.DateTime, nullable=True)
    subtotal = db.Column(db.Float, nullable=False)
    tax = db.Column(db.Float, nullable=False)
    shipping = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)

    # Relationship: Order contains multiple items (products + quantity)
    order_items = db.relationship('OrderItem', backref='order', lazy=True)

    def __repr__(self):
        return f"<Order {self.id} - {self.status}>"


# OrderItem (Intermediate Table for Order and Product with Quantity)
class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    current_unit_price = db.Column(db.Float, nullable=False)

    product = db.relationship('Product')

    def __repr__(self):
        return f"<OrderItem Order:{self.order_id} Product:{self.product_id} Qty:{self.quantity}>"




