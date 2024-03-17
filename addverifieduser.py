# Add tickets to users tickets page Simple Microservice

from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import firestore, credentials

# Intialization of Flask app and Firebase Firestore
app = Flask(__name__)
cred = credentials.Certificate("esd-ticketing-firebase-adminsdk-dxgtc-363d36e381.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route('/update-verified', methods=['POST'])
def update_verified():
    # Assuming the POST request body is JSON and contains 'ticket_id'
    data = request.get_json()
    ticket_id = data.get('ticket_id')

    if not ticket_id:
        return jsonify({"error": "Missing ticket_id"}), 400

    try:
        # Attempt to get the document reference for the specified ticket_id
        doc_ref = db.collection('tickets').document(ticket_id)

        # Update the 'verified' attribute
        doc_ref.update({"verified": True})

        return jsonify({"success": True, "message": f"Ticket {ticket_id} verified status updated."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)