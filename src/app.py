import os
from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Character, Planet, Favorite

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

@app.route('/')
def sitemap():
    return generate_sitemap(app)

# USERS
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200

@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    print("User data:", data)

    if not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({"error": "username, email and password are required"}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "username already exists"}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "email already exists"}), 400

    user = User(
        username=data['username'],
        firstname=data.get('firstname'),
        lastname=data.get('lastname'),
        email=data['email']
    )
    user.set_password(data['password'])

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(user.to_dict()), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid username or password"}), 401

    return jsonify(user.to_dict()), 200

# PEOPLE (Characters)
@app.route('/people', methods=['GET'])
def get_people():
    characters = Character.query.all()
    return jsonify([c.to_dict() for c in characters]), 200

@app.route('/people/<int:people_id>', methods=['GET'])
def get_person(people_id):
    person = Character.query.get(people_id)
    if not person:
        return jsonify({"error": "Person not found"}), 404
    return jsonify(person.to_dict()), 200

# PLANETS
@app.route('/planets', methods=['GET'])
def get_planets():
    planets = Planet.query.all()
    return jsonify([p.to_dict() for p in planets]), 200

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"error": "Planet not found"}), 404
    return jsonify(planet.to_dict()), 200

# FAVORITES for a "current user"
def get_current_user():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return None
    return User.query.get(user_id)

@app.route('/users/favorites', methods=['GET'])
def get_favorites():
    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found or user_id missing in query param"}), 404
    favorites = Favorite.query.filter_by(user_id=user.id).all()
    return jsonify([f.to_dict() for f in favorites]), 200

@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found or user_id missing in query param"}), 404
    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"error": "Planet not found"}), 404

    # Check if already favorited
    existing = Favorite.query.filter_by(user_id=user.id, planet_id=planet_id).first()
    if existing:
        return jsonify({"error": "Planet already in favorites"}), 400

    favorite = Favorite(user_id=user.id, planet_id=planet_id)
    db.session.add(favorite)
    db.session.commit()
    return jsonify(favorite.to_dict()), 201

@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_person(people_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found or user_id missing in query param"}), 404
    character = Character.query.get(people_id)
    if not character:
        return jsonify({"error": "Person not found"}), 404

    existing = Favorite.query.filter_by(user_id=user.id, character_id=people_id).first()
    if existing:
        return jsonify({"error": "Person already in favorites"}), 400

    favorite = Favorite(user_id=user.id, character_id=people_id)
    db.session.add(favorite)
    db.session.commit()
    return jsonify(favorite.to_dict()), 201

@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found or user_id missing in query param"}), 404

    favorite = Favorite.query.filter_by(user_id=user.id, planet_id=planet_id).first()
    if not favorite:
        return jsonify({"error": "Favorite not found"}), 404

    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"msg": "Favorite planet removed"}), 200

@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_person(people_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found or user_id missing in query param"}), 404

    favorite = Favorite.query.filter_by(user_id=user.id, character_id=people_id).first()
    if not favorite:
        return jsonify({"error": "Favorite not found"}), 404

    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"msg": "Favorite person removed"}), 200


if __name__ == '__main__':
    app.run(debug=True)
