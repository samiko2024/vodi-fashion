from __ini__ import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Integer, String, Text
from flask_login import UserMixin
from datetime import datetime



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), unique=True)
    password_hash = db.Column(db.String(250), nullable=False)

    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    country = db.Column(db.String(25))
    state = db.Column(db.String(25))
    note = db.Column(db.String(255))
    date_joined = db.Column(db.DateTime, default=datetime.now)

    cart_items = db.relationship('Cart', backref=db.backref('user', lazy=True))
    order_items = db.relationship('OrderItem', backref=db.backref('user', lazy=True))
    orders = db.relationship('Order', backref=db.backref('user', lazy=True))
    blogs = db.relationship('BlogPost', backref=db.backref('user', lazy=True))
    videos = db.relationship('Video', backref='user', lazy=True, cascade="all, delete-orphan")



    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password=password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password=password)

    def __str__(self):
        return '<User %r>' % User.id

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    product_price = db.Column(db.Float, nullable=False)
    product_type = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    product_desc = db.Column(db.Text(500), nullable=False)
    product_img = db.Column(db.String(1000), nullable=False)
    flash_sale = db.Column(db.Boolean, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.now)





    def __str__(self):
        return '<Product %r>' % self.product_name



class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    size = db.Column(db.String(50))
    image = db.Column(db.String(255))
    date_added = db.Column(db.DateTime, default=datetime.now)

    user_link = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __str__(self):
        return '<Cart %r>' % self.id


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    total_amount = db.Column(db.Float)
    payment_provider = db.Column(db.String(50))
    payment_reference = db.Column(db.String(255))
    payment_status = db.Column(db.String(50), default='pending')  # pending, paid, failed
    order_status = db.Column(db.String(50), default='processing')  # processing, shipped, delivered, cancelled
    date_created = db.Column(db.DateTime, default=datetime.now)
    items = db.relationship('OrderItem', backref='order', lazy=True)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    title = db.Column(db.String(120))
    price = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    size = db.Column(db.String(50))
    image = db.Column(db.String(255))

    user_link = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


    def __str__(self):
        return '<Order %r>' % self.id



class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text(1000), nullable=False)
    blog_photo = db.Column(db.String(1000), nullable=False)

    user_link = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)



class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    filename = db.Column(db.String(1000), nullable=False)
    likes = db.Column(db.Integer, default=0)
    contact_url = db.Column(db.String(255), default='#')
    comments = db.relationship('Comment', backref='video', lazy=True, cascade="all, delete-orphan")

    user_link = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"<Video {self.title}>"


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), default='Guest')
    text = db.Column(db.Text, nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    video_id = db.Column(db.Integer, db.ForeignKey("video.id"))


