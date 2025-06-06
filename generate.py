from eralchemy2 import render_er
from src.models import db

render_er(db.Model, 'diagram.png')
