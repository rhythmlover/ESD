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

# Endpoints
@app.route("/refunds/<string:event_id>")
def get_event_refunds(event_id):
    """
    Retrieves all refunds for a specific event.
    ---
    parameters:
        -   in: path
            name: event_id
            required: true
    responses:
        200:
            description: Return the refunds for the event with the specified event_id
        404:
            description: No refunds for this event found.
    """
    refunds_ref = db.collection("refunds").document(
        event_id).collection("event_refunds")
    docs = refunds_ref.stream()

    refunds = []
    for doc in docs:
        refunds.append(doc.to_dict())

    if refunds:
        return jsonify(
            {
                "code": 200,
                "data": refunds
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "No refunds for this event found."
        }
    ), 404

@app.route("/refunds/<string:event_id>/<string:ticket_id>")
def get_ticket_refund_details(event_id, ticket_id):
    """
    Retrieves refunds details for a specific ticket.
    ---
    parameters:
        -   in: path
            name: event_id
            required: true
        -   in: path
            name: ticket_id
            required: true
    responses:
        200:
            description: Return the refunds for the event with the specified event_id and ticket_id
        404:
            description: No refunds for this event found or no ticket with the specified ticket_id found.
    """
    refunds_ref = db.collection("refunds").document(
        event_id).collection("event_refunds").document(ticket_id)
    docs = refunds_ref.get()

    if docs.exists:
        data = docs.to_dict()
        return jsonify(
            {
                "code": 200,
                "data": data
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "No refunds for this event found."
        }
    ), 404


@app.route("/refunds", methods=['POST'])
def create_refund():
    """
    Create a refund request for a specific event.
    ---
    parameters:
        -   in: path
            name: event_id
            required: true
    requestBody:
        description: Refund details
        required: true
        content:
            application/json:
                schema:
                    properties:
                        user_id:
                            type: string
                            description: ID of user who requested the refund
                        ticket_id: 
                            type: number
                            description: ID of the ticket to be refunded
                        refund_status: (auto-generated)
                            type: string
                            description: Status of the refund request
    responses:
        201:
            description: Refund request created successfully
        400:
            description: Missing required fields in body
        500:
            description: Internal server error
    """
    try:
        required_fields = ['user_id', 'event_id', 'ticket_id']
        if not all(field in request.json for field in required_fields):
            return jsonify(
                {
                    "code": 400,
                    "message": "Missing required fields. Please provide user_id, ticket_id and refund_status."
                }
            ), 400

        doc_ref = db.collection("refunds").document(
            request.json['event_id']).collection("event_refunds").document(request.json['ticket_id'])
        doc_ref.set({
            'user_id': request.json['user_id'],
            'created_at': formatted_time,
            'event_id': request.json['event_id'],
            'ticket_id': request.json['ticket_id'],
            'refund_status': "pending"
        })

        return jsonify(
            {
                "code": 201,
                "message": "Refund request created successfully."
            }
        ), 201
    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred while creating the refund request. " + str(e)
            }
        ), 500


@app.route("/refunds", methods=["PUT"])
def update_refund_status():
    """
    Update a refund status for a specific ticket.
    ---
    parameters:
    requestBody:
        description: Refund status details
        required: true
        content:
            application/json:
                schema:
                    properties:
                        refund_status:
                            type: string
                            description: Status of the refund request to be updated
    responses:
        200:
            description: Refund request status updated successfully
        404:
            description: Missing required fields in body
    """
    required_fields = ['event_id', 'ticket_id', 'refund_status']
    if not all(field in request.json for field in required_fields):
        return jsonify(
            {
                "code": 404,
                "message": "Missing required fields. Please provide event_id, ticket_id, refund_status."
            }
        ), 404

    doc_ref = db.collection("refunds").document(
        request.json['event_id']).collection("event_refunds").document(request.json['ticket_id'])
    doc_ref.update({
        'refund_status': request.json['refund_status']
    })

    return jsonify(
        {
            "code": 200,
            "message": "Refund request status of ticket ID: "+ request.json['ticket_id'] + " changed to " + request.json['refund_status'] + " successfully.",
            "data": {
                "event_id": request.json['event_id'],
                "ticket_id": request.json['ticket_id']
            },
            "refund_status": request.json['refund_status']
        }
    ), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
