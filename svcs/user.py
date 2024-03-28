from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import firestore, credentials

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

@app.route('/update-verified', methods=['POST'])
def update_verified():
    data = request.json
    ticket_id = data.get('ticket_id')
    use_singpass = data.get('UEN_id')
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
        try:
            user_snapshot = user_ref.get(transaction=transaction)
            
            if user_snapshot.exists:
                current_tickets = user_snapshot.get('current_tickets') or []
                
                if ticket_id not in current_tickets:
                    current_tickets.append(ticket_id)
                    transaction.update(user_ref, {'current_tickets': current_tickets})
                    return True
                else:
                    # Ticket already exists in current_tickets
                    return True
            else:
                # User document does not exist
                return False

        except Exception as e:
            # Log the error for debugging purposes
            print(f"Error updating user's current_tickets: {e}")
            return False

    transaction = db.transaction()
    result = update_in_transaction(transaction, user_ref, ticket_id)
    
    if result:
        return jsonify({'message': 'Ticket appended to user successfully.'}), 200
    else:
        return jsonify({'error': 'Error updating user\'s current_tickets.'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)