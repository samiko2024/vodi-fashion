from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired


db = SQLAlchemy()
VODI_DB = 'database.sqlite3'

def create_database():
    db.create_all()
    print('Database Created')


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "my secret key"
    app.config['WTF_CSRF_ENABLED'] = False



    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{VODI_DB}'
    db.init_app(app)




    with app.app_context():
        create_database()


    return app