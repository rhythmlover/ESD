# Add tickets to users>current_tickets and updates tickets>age_verified to true tickets Simple Microservice

from flask import Flask, request, jsonify
import firebase_admin
import requests
from firebase_admin import firestore, credentials
import verifytickets


# Intialization of Flask app and Firebase Firestore
app = Flask(__name__)
cred = credentials.Certificate("esd-ticketing-firebase-adminsdk-dxgtc-363d36e381.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Flask route to update verified status and append ticket ID to user's current_tickets
@app.route('/update-verified', methods=['POST'])

def update_verified():
    ticket_id = request.args.get('ticket_id')
    use_singpass = request.args.get('UEN')
    if not ticket_id:
        return jsonify({'error': 'Missing ticket_id'}), 400

    try:
        # Attempt to get the ticket document to verify it exists and get the associated user_id
        ticket_doc_ref = db.collection('tickets').document(ticket_id)
        ticket_doc = ticket_doc_ref.get()

        if not ticket_doc.exists:
            return jsonify({"message": "Ticket not found"}), 404
        
        # Update the ticket's age_verified field
        if use_singpass:
            ticket_doc_ref.update({"age_verified": True})

        # Assuming ticket document contains a 'user_id'
        user_id = ticket_doc.to_dict().get('user_id')
        if user_id:
            # Perform the transaction to append the ticket_id to the user's current_tickets
            transaction_result = append_ticket_to_user(user_id, ticket_id)
            if transaction_result:
                return jsonify({"message": f"Ticket {ticket_id} verified and added to user {user_id}."}), 200
            else:
                return jsonify({"error": "Failed to update user's current_tickets."}), 500
        else:
            return jsonify({"message": "User ID not found in ticket"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def append_ticket_to_user(user_id, ticket_id):
    user_ref = db.collection('users').document(user_id)

    @firestore.transactional
    def update_in_transaction(transaction, user_ref, ticket_id):
        user_snapshot = user_ref.get(transaction=transaction)
        if user_snapshot.exists:
            current_tickets = user_snapshot.get('current_tickets') or []
            if ticket_id not in current_tickets:
                current_tickets.append(ticket_id)
                transaction.update(user_ref, {'current_tickets': current_tickets})
                return True
        return False

    transaction = db.transaction()
    return update_in_transaction(transaction, user_ref, ticket_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5009, debug=True)
