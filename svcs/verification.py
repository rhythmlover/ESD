# Verify Ticket Simple Microservice - check if redeemed {ticket_id}

from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import firestore, credentials

# Intialization of Flask app and Firebase Firestore
app = Flask(__name__)
cred = credentials.Certificate("esd-ticketing-firebase-adminsdk-dxgtc-363d36e381.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

#Use Flask's app.route decorator to map the URL route /event to the function get_all
#To call this function, the URL to use is for GET
@app.route('/get-ticket-status/<string:ticket_id>/<string:qr_code>', methods=['GET'])
def get_ticket_status_route(ticket_id, qr_code):
    """
    abc
    """

    if not ticket_id or not qr_code:
        return jsonify({'error': 'Missing ticket_id/QR code'}), 400

    # Attempt to get the document from the collection "tickets" by ticket_id
    doc_ref = db.collection('tickets').document(ticket_id)
    doc = doc_ref.get()

    if doc.exists:
        if doc.to_dict().get("qr_code") != qr_code:
            return jsonify(
            {
                "code": 400,
                "message": "QR Code does not match."
            }), 400

        # If the document exists, return the status field
        status = doc.to_dict().get('status', False)
        return jsonify({
            "code": 200,
            "data": {
                "ticket_id": ticket_id,
                "status": status
            }
        })
    else:
        # If no document exists for the given ticket_id, return an appropriate message
        return jsonify(
            {
                "code": 404,
                "data": {
                    "ticket_id": ticket_id
                },
                "message": "Ticket not found."
            }
        ), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5009, debug=True)