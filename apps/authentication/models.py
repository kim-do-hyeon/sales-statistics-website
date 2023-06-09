# -*- encoding: utf-8 -*-
from flask_login import UserMixin
from apps import db, login_manager
from apps.authentication.util import hash_pass
class Users(db.Model, UserMixin):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(64), unique=True)
    password = db.Column(db.LargeBinary)
    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]
            if property == 'password':
                value = hash_pass(value)
            setattr(self, property, value)
    def __repr__(self):
        return str(self.username)

class Excel_Data(db.Model, UserMixin) :
    __tablename__ = 'excel_data'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.Text)
    active = db.Column(db.Integer)

class Product_Data(db.Model, UserMixin) :
    __tablename__ = 'product_excel'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.Text)
    active = db.Column(db.Integer)

class Product_Details(db.Model, UserMixin) :
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Text)
    name = db.Column(db.Text)
    standard = db.Column(db.Text)
    standard_secondary = db.Column(db.Text)

class Option(db.Model, UserMixin) :
    __tablename__ = 'options'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Text)

@login_manager.user_loader
def user_loader(id):
    return Users.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = Users.query.filter_by(username=username).first()
    return user if user else None
