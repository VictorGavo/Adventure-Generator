from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from passlib.hash import bcrypt
import openai


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
    focus = db.Column(db.String, nullable=False)
    biome_id = db.Column(db.Integer, db.ForeignKey('biome.id'), nullable=False)
    biome = relationship("Biome")
    vibe = db.Column(db.String, nullable=False)
    box_text = db.Column(db.String)
    image_text = db.Column(db.String)

    def __init__(self, focus, biome_id, vibe):
        self.focus = focus
        self.biome_id = biome_id
        self.vibe = vibe

    def generate_description(self, biome):
        prompt = f"""As a scene generator for TTRPGs, your task is to construct a captivating scene based on the given parameters: 
        biome ({biome}), vibe ({self.vibe}), and focus ({self.focus}). Craft two paragraphs: one optimized for image generation, 
        evoking vivid imagery (<= 300 characters), and the other for the GM to read aloud, using descriptive language to 
        capture the specified feeling. Please avoid including any titles or headings in the generated text."""

        response = openai.Completion.create(
            engine="text-davinci-003",  # Replace with the desired engine (e.g., davinci, curie, etc.)
            prompt=prompt,
            max_tokens=500  # Set the desired maximum number of tokens in the completion
        )

        paragraphs = response.choices[0].text.strip().split("\n\n")
        if len(paragraphs) >= 2:
            image_gen = paragraphs[0]
            gm_desc = paragraphs[1]
        else:
            image_gen = "error"
            gm_desc = "error"

        self.image_text = image_gen
        self.box_text = gm_desc


    def __repr__(self):
        return f'Scene {self.focus} has been added to the {self.biome.name } database'