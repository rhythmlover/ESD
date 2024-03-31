from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import firestore, credentials
from datetime import datetime
import pyqrcode
import uuid
import os

# Intialization of Flask app and Firebase Firestore
app = Flask(__name__)
cred = credentials.Certificate("esd-ticketing-firebase-adminsdk-dxgtc-363d36e381.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Global variables
now = datetime.now()
formatted_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")

# Endpoints
@app.route("/tickets", methods=['GET'])
def get_all_tickets():
    """
    Retrieves account details of a specific user.
    ---
    responses:
        200:
            description: Return all tickets
        404:
            description: No tickets found.
    """
    users_ref = db.collection("tickets")
    ticketlist = users_ref.stream()
    
    data = []
    for ticket in ticketlist:
        data.append(ticket.to_dict())

    if len(data):
        return jsonify(
            {
                "code": 200,
                "data": data
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "No tickets found."
        }
    ), 404

@app.route("/tickets/<string:ticket_id>", methods=['GET'])
def get_specific_ticket(ticket_id):
    """
    Retrieves ticket details of a specific ticket id
    ---
    responses:
        200:
            description: Return the ticket details of the ticket with the specified ticket_id
        404:
            description: No ticket with the specified ticket_id found.
    """
    users_ref = db.collection("tickets").document(ticket_id)
    ticket_details = users_ref.get()

    if ticket_details.exists:
        data = ticket_details.to_dict()
        return jsonify(
            {
                "code": 200,
                "data": data
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "No ticket with the specified ticket_id found"
        }
    ), 404

@app.route("/tickets/create", methods=['POST'])
def create_ticket():
    """
    Create a ticket for a specific event.
    ---
    requestBody:
        description: Refund submission details
        required: true
        content:
            application/json:
                schema:
                    properties:
                        user_id:
                            type: string
                            description: ID of the user
                        event_id:
                            type: string
                            description: ID of the event
                        ticket_id:
                            type: string
                            description: ID of the ticket
                        qr_code:
                            type:string
                            description: QR code of the ticket
    responses:
        201:
            description: Ticket created successfully
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
                    "message": "Missing required fields. Please provide user_id, event_id, ticket_id."
                }
            ), 400
        
        # Generate QR code string
        qr_code_base64 = generate_qr_code(request.json)
        
        doc_ref = db.collection("tickets").document(request.json['ticket_id'])
        doc_ref.set({
            'user_id': request.json['user_id'],
            'created_at': formatted_time,
            'event_id': request.json['event_id'],
            'ticket_id': request.json['ticket_id'],
            'age_verified': False,
            'ticket_redeemed': False,
            'payment_id': "",
            "charge_id": "",
            "qr_code": qr_code_base64,
        })

        return jsonify(
            {
                "code": 201,
                "message": "Ticket created successfully."
            }
        ), 201
    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred during ticket creation. " + str(e)
            }
        ), 500
    
@app.route("/tickets/<string:ticket_id>/age_verify", methods=["PUT"])
def update_age_verification(ticket_id):
    """
    Update the age verification status of a ticket.
    ---
    parameters:
        -   in: path
            name: ticket_id
            required: true
    requestBody:
        description: Age verification details
        required: true
        content:
            application/json:
                schema:
                    properties:
                        age_verified:
                            type: boolean
                            description: Age verification status to be updated
    responses:
        200:
            description: Age verification status updated successfully
        404:
            description: Missing required fields in body
    """
    required_fields = ['age_verified']
    if not all(field in request.json for field in required_fields):
        return jsonify(
            {
                "code": 404,
                "message": "Missing required fields. Please provide age_verified."
            }
        ), 404

    doc_ref = db.collection("tickets").document(ticket_id)
    doc_ref.update({
        'age_verified': request.json['age_verified']
    })

    return jsonify(
        {
            "code": 200,
            "message": "Ticket ID: " + str(ticket_id) + "'s age verification status updated successfully to " + str(request.json['age_verified']) + "."
        }
    ), 200

@app.route("/tickets/<string:ticket_id>/redeem", methods=["POST"])
def update_ticket_redeem(ticket_id):
    """
    Update the redemption status of a ticket.
    ---
    parameters:
        -   in: path
            name: ticket_id
            required: true
    requestBody:
        description: Redemption details
        required: true
        content:
            application/json:
                schema:
                    properties:
                        ticket_redeemed:
                            type: boolean
                            description: Redemption status to be updated
    responses:
        200:
            description: Redemption status updated successfully
        404:
            description: Missing required fields in body
    """
    required_fields = ['ticket_redeemed']
    if not all(field in request.json for field in required_fields):
        return jsonify(
            {
                "code": 404,
                "message": "Missing required fields. Please provide ticket_redeemed."
            }
        ), 404

    doc_ref = db.collection("tickets").document(ticket_id)
    doc_ref.update({
        'ticket_redeemed': request.json['ticket_redeemed']
    })

    return jsonify(
        {
            "code": 200,
            "message": "Ticket ID: " + str(ticket_id) + "'s redemption status updated successfully to " + str(request.json['ticket_redeemed']) + "."
        }
    ), 200

@app.route("/tickets/<string:ticket_id>/payment", methods=["PUT"])
def update_payment_id(ticket_id):
    """
    Update the payment ID and charge ID of a ticket.
    ---
    parameters:
        -   in: path
            name: ticket_id
            required: true
    requestBody:
        description: Redemption details
        required: true
        content:
            application/json:
                schema:
                    properties:
                        payment_id:
                            type: string
                            description: Payment ID to be updated
                        charge_id:
                            type: string
                            description: Charge ID to be updated
    responses:
        200:
            description: Payment ID and Charge ID updated successfully
        404:
            description: Missing required fields in body
    """
    required_fields = ['payment_id', 'charge_id']
    if not all(field in request.json for field in required_fields):
        return jsonify(
            {
                "code": 404,
                "message": "Missing required fields. Please provide payment_id and charge_id."
            }
        ), 404

    doc_ref = db.collection("tickets").document(ticket_id)
    doc_ref.update({
        'payment_id': request.json['payment_id'],
        'charge_id': request.json['charge_id']
    })

    return jsonify(
        {
            "code": 200,
            "message": "Ticket ID: " + str(ticket_id) + "'s payment ID and charge ID updated successfully to " + str(request.json['payment_id']) + " and " + str(request.json['charge_id']) + " respectively."
        }
    ), 200

def generate_qr_code(ticket_data):
    try:
        # Generate unique QR code based on user id, event id and ticket id
        qr_data = f"{ticket_data['user_id']}|{ticket_data['event_id']}|{ticket_data['ticket_id']}"
        qr = pyqrcode.create(qr_data)
        qr_code_base64 = qr.png_as_base64_str(scale=8)
        return qr_code_base64
    except Exception as e:
        print("Error generating QR code:", str(e))
        return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
