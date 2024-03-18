import stripe
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

stripe.api_key = "sk_test_51OsyUO2LHSKllIVVLicsqNteZkHVwC6ViXLkEJtMTqxPVa3paUucKASoYfiIKGB06v3Atrf1UMmQ41kg1F3c8SIH00RBqtmlXJ"

@app.route("/process_payment", methods=['POST'])
def process_payment():
    if request.is_json:
        try:
            payment_data = request.get_json()

            payment_intent = stripe.PaymentIntent.create(
                amount = payment_data.get('amount'),
                currency = payment_data.get('currency'),
                payment_method = payment_data.get('payment_method_id'),
                confirm=True,
                return_url="http://localhost/IS213/ESD/PurchaseTickets/index.html",
            )

            return jsonify({
                "code": 200,
                "message": "Payment processed successfully.",
                "payment_intent_id": payment_intent.id,
                "requires_action": payment_intent.status == "requires_action",
                "next_action": payment_intent.next_action
            }), 200

        except stripe.error.StripeError as e:
            return jsonify({
                "code": 400,
                "message": str(e)
            }), 400

        except Exception as e:
            return jsonify({
                "code": 500,
                "message": f"Internal server error: {str(e)}"
            }), 500
    else:
        return jsonify({
            "code": 400,
            "message":
            "Invalid JSON input."}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)