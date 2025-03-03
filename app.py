import os
from dotenv import load_dotenv  # For local testing
load_dotenv()
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
from flask_cors import CORS  # For handling CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model
class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(100), unique=True, nullable=False)
    members = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'team_name': self.team_name,
            'members': self.members,
            'timestamp': self.timestamp.isoformat()
        }

# Create database tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/register', methods=['POST'])
def register_team():
    data = request.get_json()
    
    # Validate input
    if not data or 'teamName' not in data or 'members' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check for duplicate team name
    if Team.query.filter_by(team_name=data['teamName']).first():
        return jsonify({'error': 'Team name already exists'}), 409
    
    # Save to database
    new_team = Team(
        team_name=data['teamName'],
        members=data['members']
    )
    
    try:
        db.session.add(new_team)
        db.session.commit()
        return jsonify({'message': 'Registration successful!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Database error'}), 500

@app.route('/order', methods=['GET'])
def get_order():
    # Get all teams
    teams = Team.query.all()
    
    # Get mode from query parameter
    mode = request.args.get('mode', 'random').lower()
    
    # Convert teams to list of dicts
    teams_list = [team.to_dict() for team in teams]
    
    # Apply ordering
    if mode == 'fcfs':
        # Sort by timestamp
        ordered = sorted(teams_list, key=lambda x: x['timestamp'])
    else:
        # Random shuffle (Fisher-Yates)
        random.shuffle(teams_list)
        ordered = teams_list
    
    return jsonify(ordered)

if __name__ == '__main__':
    app.run(debug=True, port=5000)