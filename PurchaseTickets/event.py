#import Flask, request, jsonify from library flask
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import firestore, credentials
from datetime import datetime

# Intialization of Flask app and Firebase Firestore
app = Flask(__name__)
CORS(app)
cred = credentials.Certificate("esd-ticketing-firebase-adminsdk-dxgtc-363d36e381.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Endpoints
# Retrieves all events
@app.route("/events", methods=['GET'])
def get_all_events():
    """
    Retrieves all events.
    ---
    responses:
        200:
            description: Return all events
        404:
            description: No events found.
    """
    events_ref = db.collection("events")
    eventlist = events_ref.stream()
    
    data = []
    for event in eventlist:
        data.append(event.to_dict())

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
            "message": "No events found."
        }
    ), 404

@app.route("/events/<string:event_id>", methods=['GET'])
#Retrieves account details of a specific user.
def find_by_event_id(event_id):
    """
    Retrieves event details of a specific event.
    ---
    parameters:
        -   in: path
            name: event_id
            required: true
    responses:
        200:
            description: Return the event details of the event with the specified event_id
        404:
            description: No event with the specified event_id found.
    """

    event_details = db.collection("events").document(event_id).get()

    if event_details.exists:
        data = event_details.to_dict()
        return jsonify(
            {
                "code": 200,
                "data": data
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "No event with the specified event_id found."
        }
    ), 404


@app.route("/events/<string:event_id>", methods=['POST'])
def create_event(event_id):
    """
    Create a specific event.
    ---
    parameters:
        -   in: path
            name: event_id
            required: true
    requestBody:
        description: Review details
        required: true
        content:
            application/json:
                schema:
                    properties:
                        event_datetime: 
                            type: timestamp
                            description: Date & Time of event to be created
                        event_description: 
                            type: string
                            description: Description of event to be created
                        event_image:
                            type: string
                            description: URL of event image to be created
                        event_name:
                            type: string
                            description: Name of event to be created
                        event_price: 
                            type: number
                            description: Price of event to be created
    responses:
        201:
            description: Event created successfully
        400:
            description: Missing required fields in body
        500:
            description: Internal server error
    """

    try:
        required_fields = ['event_datetime', 'event_description', 'event_image', 'event_name', 'event_price']
        if not all(field in request.json for field in required_fields):
            return jsonify(
                {
                    "code": 400,
                    "message": "Missing required fields. Please fill in all fields."
                }
            ), 400

        #check events
        doc_ref = db.collection("events").document(event_id)
        #.collection("events").document()
        if doc_ref.get().exists:
            return jsonify(
                {
                    "code": 400,
                    "message": "Event with the specified event_id already exists."
                }
            ), 400
        doc_ref.set({
            'event_datetime': request.json['event_datetime'],
            'event_description': request.json['event_description'],
            'event_id': event_id,
            'event_image': request.json['event_image'],
            'event_name': request.json['event_name'],
            'event_price': request.json['event_price']
        })
        return jsonify(
            {
                "code": 201,
                "message": "Event created successfully."
            }
        ), 201
    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred while creating the event. " + str(e)
            }
        ), 500
 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)