import stripe
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import firestore, credentials
from datetime import datetime

# Intialization of Flask app and Firebase Firestore
app = Flask(__name__)
cred = credentials.Certificate("esd-ticketing-firebase-adminsdk-dxgtc-363d36e381.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Global variables
now = datetime.now()
formatted_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")
stripe.api_key = "sk_test_51OtVqgKfHG7YK88cdJNGkMVFtQPKWij5Pw7TbjwqK2raomL5XHd5xWvJaHYt0mRauvw2wKBZbtmo4MFi0KxtIlLF001kl4HcOC"

# Endpoints
@app.route("/submit_refund", methods=['POST'])
def create_refund():
    """
    Create a refund request for a specific event.
    ---
    requestBody:
        description: Refund submission details
        required: true
        content:
            application/json:
                schema:
                    properties:
                        charge_id:
                            type: string
                            description: ID of the stripe charge to be refunded
    responses:
        201:
            description: Refund request submitted successfully
        400:
            description: Missing required fields in body
        500:
            description: Internal server error
    """
    try:
        required_fields = ['charge_id']
        if not all(field in request.json for field in required_fields):
            return jsonify(
                {
                    "code": 400,
                    "message": "Missing required fields. Please provide charge_id."
                }
            ), 400

        stripe.Refund.create(charge=request.json['charge_id'])

        return jsonify(
            {
                "code": 201,
                "message": "Refund request submitted successfully."
            }
        ), 201
    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred while submitting the refund request. " + str(e)
            }
        ), 500
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)