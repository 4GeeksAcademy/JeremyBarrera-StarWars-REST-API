import os
import sys
import enum
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class SerializerMixin:
    def to_dict(self):
        d = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        if 'password_hash' in d:
            d.pop('password_hash')
        return d

class MediaType(enum.Enum):
    image = "image"
    video = "video"

class Follower(db.Model, SerializerMixin):
    __tablename__ = 'follower'
    user_from_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    user_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

class User(db.Model, SerializerMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    firstname = db.Column(db.String(50))
    lastname = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    posts = db.relationship('Post', back_populates='user', cascade='all, delete-orphan')
    comments = db.relationship('Comment', back_populates='author', cascade='all, delete-orphan')
    followers = db.relationship('Follower', foreign_keys=[Follower.user_to_id], backref='followed', cascade='all, delete-orphan')
    following = db.relationship('Follower', foreign_keys=[Follower.user_from_id], backref='follower', cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='user', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Post(db.Model, SerializerMixin):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', back_populates='posts')
    comments = db.relationship('Comment', back_populates='post', cascade='all, delete-orphan')
    media = db.relationship('Media', back_populates='post', cascade='all, delete-orphan')

class Comment(db.Model, SerializerMixin):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    comment_text = db.Column(db.String(500), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    author = db.relationship('User', back_populates='comments')
    post = db.relationship('Post', back_populates='comments')

class Media(db.Model, SerializerMixin):
    __tablename__ = 'media'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(MediaType), nullable=False)
    url = db.Column(db.String(250), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    post = db.relationship('Post', back_populates='media')

class Character(db.Model, SerializerMixin):
    __tablename__ = 'character'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(20))
    birth_year = db.Column(db.String(20))
    eye_color = db.Column(db.String(20))
    height = db.Column(db.String(20))

    favorites = db.relationship('Favorite', back_populates='character', cascade='all, delete-orphan')

class Planet(db.Model, SerializerMixin):
    __tablename__ = 'planet'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    climate = db.Column(db.String(50))
    terrain = db.Column(db.String(50))
    population = db.Column(db.String(50))

    favorites = db.relationship('Favorite', back_populates='planet', cascade='all, delete-orphan')

class Favorite(db.Model, SerializerMixin):
    __tablename__ = 'favorite'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=True)
    planet_id = db.Column(db.Integer, db.ForeignKey('planet.id'), nullable=True)

    character = db.relationship('Character', back_populates='favorites')
    planet = db.relationship('Planet', back_populates='favorites')
