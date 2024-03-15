from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/process_payment", methods=['POST'])
def process_payment():
    if request.is_json:
        try:
            payment_data = request.get_json()
            print("\nReceived a payment request:", payment_data)

            # Code to process payment
            # Example: integrate with Stripe API to process payments
            
            return jsonify({"code": 200, "message": "Payment processed successfully."}), 200

        except Exception as e:
            return jsonify({"code": 500, "message": "Internal server error: " + str(e)}), 500

    return jsonify({"code": 400, "message": "Invalid JSON input."}), 400

if __name__ == "__main__":
    print("This is Flask " + os.path.basename(__file__) + " for processing payments...")
    app.run(host="0.0.0.0", port=5002, debug=True)
