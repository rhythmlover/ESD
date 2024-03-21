#import Flask, request, jsonify from library flask
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import firestore, credentials
from datetime import datetime

# Intialization of Flask app and Firebase Firestore
app = Flask(__name__)
cred = credentials.Certificate("esd-ticketing-firebase-adminsdk-dxgtc-363d36e381.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

"""
#We create a new class event, which inherits from a basic database model, provided by SQLAlchemy.
class Event(db.Model):
    #Specify the table name as event 
    __tablename__ = 'event'

    #define data column name, type and if it is nullable (able to not enter input)
    #add (number) after db.String to limit the length
    #YYYYMMDDHHMMSS
    event_datetime = db.Column(db.DateTime, nullable=False) #may need to check datatype for this
    event_description = db.Column(db.String(64), nullable=False)
    event_id = db.Column(db.String(64), primary_key=True)
    event_image = db.Column(db.String(precision=2), nullable=False)
    event_name = db.Column(db.String(64), nullable=False)
    event_price = db.Column(db.Float(precision=2), nullable=False)
    
    #Specify the properties of a event when it is created
    def __init__(self, event_datetime, event_description, event_id, event_image, event_name, event_price):
        #YYYYMMDDHHMMSS
        self.event_datetime = event_datetime
        self.event_description = event_description
        self.event_id = event_id
        self.event_image = event_image
        self.event_name = event_name
        self.event_price = event_price
        

    #Represent our event object as a JSON string
    def json(self):
        return {"event_id": self.event_id, "event_name": self.event_name, "event_price": self.event_price, "event_datetime": self.event_datetime}
"""

"""
#Use Flask's app.route decorator to map the URL route /event to the function get_all
#To call this function, the URL to use is for GET
@app.route("/event")
def get_all():
    #SQLAlchemy provides a session.scalars attribute to retrieve all records from the book table using db.select(Book).all(); this returns a list, which we assign to booklist
    eventlist = db.session.scalars(db.select(Event)).all()

    if len(eventlist):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "events": [event.json() for event in eventlist]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no events."
        }
    ), 404
"""

"""
#Use Flask's app.route decorator to map the URL route /event/<string:event_id> to the function find_by_event_id
#To call this function, the URL to use is for GET
@app.route("/event/<string:event_id>")
def find_by_event_id(event_id):
    #Retrieve only the event with the event_id specified in the path variable, similar to the WHERE clause in a SQL SELECT expression
    event = db.session.scalars(
    	db.select(Event).filter_by(event_id=event_id).
    	limit(1)
        ).first()
    #Use first() to return 1 event or None if there is no matching events. This is similar to the LIMIT 1 clause in SQL

#If the book is found (not None), return its JSON representation. In addition, return HTTP status code 200 for NOT FOUND.
    if event:
        return jsonify(
            {
                "code": 200,
                "data": event.json()
            }
        )

#Else, return an error message in JSON. In addition, return HTTP status code 404 for NOT FOUND.
    return jsonify(
        {
            "code": 404,
            "message": "Event not found."
        }
    ), 404
"""

"""
#Use Flask's app.route decorator to map the URL route /event/<string:event_id> to the function find_by_event_id
#To call this function, the URL to use is for POST
@app.route("/event/<string:event_id>", methods=['POST'])
def create_event(event_id):
    #check if the event already exists in the table
    if (db.session.scalars(
    	db.select(Event).filter_by(event_id=event_id).
    	limit(1)
        ).first()
        ):
        #If event exist, return an error message in JSON with HTTP status code 400 BAD REQUEST
        return jsonify(
            {
                "code": 400,
                "data": {
                    "event_id": event_id
                },
                "message": "Event already exists."
            }
        ), 400
    
    #Details of the event have to be sent in the body of the request in JSON format
    data = request.get_json()
    #Then we create an instance of a event using the event_id and the attributes sent in the request (**data)
    #** is a common idiom to allow an arbitrary number of arguments to a function
    event = Event(event_id, **data)

    try:
        #To add the event to the table and commit the changes, we use the db.session object (provided by SQLAlchemy) 
        #YYYYMMDDHHMMSS
        db.session.add(event)
        db.session.commit()
    except:
        return jsonify(
            {
                "code": 500,
                "data": {
                    "event_id": event_id
                },
                "message": "An error occurred creating the event."
            }
        ), 500

#If there is no exception, we return the JSON representation of the event we have added with HTTP status code 201 - CREATED
    return jsonify(
        {
            "code": 201,
            "data": event.json()
        }
    ), 201
"""

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
                        event_id:
                            type: string
                            description: ID of event to be created
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
        required_fields = ['event_datetime', 'event_description', 'event_id', 'event_image', 'event_name', 'event_price']
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