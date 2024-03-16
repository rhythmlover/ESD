import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost:3306/user'  # Adjust database URI accordingly
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}
db = SQLAlchemy(app)

# Database Model for User
class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)

    def json(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
        }

@app.route("/user/<int:user_id>", methods=['GET'])
def get_user(user_id):
    user = User.query.filter_by(user_id=user_id).first()
    if user:
        return jsonify({
            "code": 200,
            "data": user.json()
        }), 200
    else:
        return jsonify({
            "code": 404,
            "message": "User not found."
        }), 404

if __name__ == '__main__':
    print("This is Flask for " + os.path.basename(__file__) + ": providing user information...")
    app.run(host='0.0.0.0', port=5004, debug=True)
