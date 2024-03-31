from flask import Flask, request, jsonify
from datetime import datetime
import firebase_admin
from firebase_admin import firestore, credentials
from flask_cors import CORS 

# Intialization of Flask app and Firebase Firestore
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes in the app
cred = credentials.Certificate(
    "esd-ticketing-firebase-adminsdk-dxgtc-363d36e381.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Global variables
now = datetime.now()
formatted_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")

@app.route("/attendance/events/<string:event_id>", methods=['GET'])
def event_attendance(event_id):
    """
    Get attendance of an event
    ---
    parameters:
        -   in: path
            name: event_id
            required: true
    responses:
        200:
            description: Return the attendance of all user_ids that attended
        404:
            description: No attendance found for event

    """
    doc_ref = db.collection("event_attendance").document(event_id).collection("users")
    docs = doc_ref.stream()

    attendance_for_event = []
    for doc in docs:
        attendance_for_event.append(doc.to_dict())

    if attendance_for_event:
        return jsonify(
            {
                "code": 200,
                "data": attendance_for_event
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "No attendance for this event found."
        }
    ), 404

@app.route("/attendance/events/<string:event_id>", methods=['POST'])
def add_user_to_event_attendance(event_id):
    """
    Add user to Event Attendance
    ---
    parameters:
        - in: path
          name: event_id
          user_id: user_id
          required: true
          description: The ID of the event to add users into
          schema:
            type: string
            example: "765"
    requestBody:
        description: Ticket confirmation details
        required: true
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        user_id:
                            type: string
                            description: The ID of the user to add to the event attendance
                            example: "456"

    responses:
        201:
            description: User's attendance added successfully.
        400:
            description: Invalid request or missing parameters.
        500:
            description: An error occurred during event attendance creation.
    """
    try:
        required_fields = ['user_id']
        if not all(field in request.json for field in required_fields):
            return jsonify(
                {
                    "code": 400,
                    "message": "Missing required fields. Please provide user_id."
                }
            ), 400

        doc_ref = db.collection("event_attendance").document(
            event_id).collection("users").document(request.json['user_id'])
        doc_ref.set({
            'check_in_timing': formatted_time,
            'user_id': request.json['user_id'],
            'event_id': event_id
        })

        return jsonify(
            {
                "code": 201,
                "message": "User's attendance to event added successfully."
            }
        ), 201
    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred while adding user's attendance to event. " + str(e)
            }
        ), 500

@app.route("/attendance/users/<string:user_id>", methods=['GET'])
def get_user_event_attendance_history(user_id):
    """
    Get attendance of a User's Event Attendance History
    ---
    parameters:
        -   in: path
            name: user_id
            required: true
    responses:
        200:
            description: Return the attendance of all events that user attended
        404:
            description: user not found

    """
    docs_ref = db.collection("users_event_attendance").document(user_id)
    docs = docs_ref.get()

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
            "message": "User ID not found."
        }
    ), 404

@app.route("/attendance/users/<string:user_id>", methods=['POST'])
def add_event_to_user_event_history(user_id):
    """
    Add event attendance to User User's Event Attendance History
    ---
    parameters:
        -   in: path
            name: user_id
            required: true
    requestBody:
        description: User's event details
        required: true
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        event_id:
                            type: string
                            description: The ID of the event being added to the user's attendance history
                            example: "456"

    responses:
        201:
            description: Event added to user's attendance history successfully.
        400:
            description: Invalid request or missing parameters.
        500:
            description: An error occurred during event attendance creation.
    """
    try:
        required_fields = ['event_id']
        if not all(field in request.json for field in required_fields):
            return jsonify(
                {
                    "code": 400,
                    "message": "Missing required fields. Please provide event_id."
                }
            ), 400

        doc_ref = db.collection("users_event_attendance").document(user_id)
        doc = doc_ref.get()

        if doc.exists:
            doc_ref.update({"events_attended": firestore.ArrayUnion([request.json['event_id']])})
        else:
            doc_ref.set({"events_attended": [request.json['event_id']]})


        return jsonify(
            {
                "code": 201,
                "message": "Event added to user's event history successfully."
            }
        ), 201
    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred while adding event to user's event history. " + str(e)
            }
        ), 500
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)
