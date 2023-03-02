from datetime import datetime
from flask_login import UserMixin
from passlib.hash import bcrypt


from src import db


class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)

    def __init__(self, email, password):
        self.email = email
        self.password = bcrypt.hash(password)
        self.created_on = datetime.now()

    def __repr__(self):
        return f"<email {self.email}>"
    
class Biome(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    scene = db.relationship("Scene", cascade="all, delete-orphan")

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __init__(self, name, description, user_id):
        self.name = name
        self.description = description
        self.user_id = user_id

    def __repr__(self):
        return f'Biome {self.name} has been added to the database'
    
class Scene(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    biome_id = db.Column(db.Integer, db.ForeignKey('biome.id'), nullable=False)
    creature = db.Column(db.String)

    def __init__(self, name, description, biome_id, creature=''):
        self.name = name
        self.description = description
        self.biome_id = biome_id
        self.creature = creature

    def __repr__(self):
        return f'Scene {self.name} has been added to the {self.biome.name } database'