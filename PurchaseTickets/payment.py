import stripe
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Assuming you have set STRIPE_SECRET_KEY in your environment variables
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

@app.route("/process_payment", methods=['POST'])
def process_payment():
    if request.is_json:
        try:
            payment_data = request.get_json()
            # Example Stripe charge creation (ensure you handle real payment data securely)
            # charge = stripe.Charge.create(
            #     amount=1000,  # $10.00 this should be dynamically set
            #     currency='usd',
            #     source=payment_data['token'],
            #     description='Ticket purchase',
            # )
            return jsonify({"code": 200, "message": "Payment processed successfully."}), 200
        except Exception as e:
            return jsonify({"code": 500, "message": "Internal server error: " + str(e)}), 500

    return jsonify({"code": 400, "message": "Invalid JSON input."}), 400