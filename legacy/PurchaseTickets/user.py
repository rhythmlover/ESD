from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import firestore, credentials
from datetime import datetime

# Intialization of Flask app and Firebase Firestore
app = Flask(__name__)
CORS(app)
cred = credentials.Certificate("esd-ticketing-firebase-adminsdk-dxgtc-363d36e381.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Endpoints
@app.route("/users/<string:user_id>", methods=['GET'])
def get_user_details(user_id):
    """
    Retrieves account details of a specific user.
    ---
    parameters:
        -   in: path
            name: user_id
            required: true
    responses:
        200:
            description: Return the account details of the user with the specified user_id
        404:
            description: No user with the specified user_id found.
    """
    users_ref = db.collection("users").document(user_id)
    user_details = users_ref.get()

    if user_details.exists:
        data = user_details.to_dict()
        return jsonify(
            {
                "code": 200,
                "data": data
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "No user with the specified user_id found."
        }
    ), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)