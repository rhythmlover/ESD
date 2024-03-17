# app

from flask import Flask, render_template
from flask_cors import CORS
from verifytickets import update_age_verified
from verifytickets import verify_ticket

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template('homepage.html')