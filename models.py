from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import func, cast, Integer, case
from sqlalchemy.orm import relationship
from sqlalchemy.types import Float
from passlib.hash import bcrypt
import openai


from src import db


class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)
    biomes = db.relationship("Biome", backref="user", lazy=True)

    def __init__(self, email, username, password):
        self.email = email
        self.username = username
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
    shared = db.Column(db.Boolean, default=False)
    total_votes = db.Column(db.Integer, default=0)
    avg_vote = db.Column(db.Float, default=0.0)
    votes = relationship('Vote', backref='voted_scene', lazy=True)
    comment_count = db.Column(db.Integer, default=0)

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

    def update_comment_count(self):
        self.comment_count = Comment.query.filter_by(scene_id=self.id).count()
        db.session.commit()

    def update_vote_stats(self):
        result = db.session.query(
            db.func.count(Vote.id).label('total_votes'),
            db.func.avg(db.cast(Vote.is_upvote, db.Integer)).label('avg_vote')
        ).filter_by(scene_id=self.id).first()

        self.total_votes = result.total_votes
        self.avg_vote = result.avg_vote

        db.session.commit()

    @property
    def avg_vote(self):
        vote_sum = db.session.query(func.sum(case((Vote.is_upvote == True, cast(1.0, Float))), else_=cast(0.0, Float))).filter_by(scene_id=self.id).scalar()
        vote_count = db.session.query(func.count(Vote.id)).filter_by(scene_id=self.id).scalar()
        if vote_sum is not None and vote_count > 0:
            avg_vote = vote_sum / vote_count
            formatted_avg_vote = "{:.2f}".format(avg_vote)  # Format to 2 decimal places
            return float(formatted_avg_vote)
        else:
            return 0.0

    def __repr__(self):
        return f'Scene {self.focus} has been added to the {self.biome.name } database'
    
class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    scene_id = db.Column(db.Integer, db.ForeignKey('scene.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow())

    user = relationship('User')
    scene = relationship('Scene')

    @property
    def username(self):
        return self.user.username if self.user else None

class Vote(db.Model):
    __tablename__ = 'votes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    scene_id = db.Column(db.Integer, db.ForeignKey('scene.id'))
    is_upvote = db.Column(db.Boolean)

    user = db.relationship('User')
    scene = db.relationship('Scene')