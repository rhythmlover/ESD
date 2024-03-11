from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from os import environ

# set dbURL=mysql+mysqlconnector://root@localhost:3306/event

from flasgger import Swagger


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)


# Initialize flasgger 
app.config['SWAGGER'] = {
    'title': 'Attendance microservice API',
    'version': 1.0,
    "openapi": "3.0.2",
    'description': 'Allows retrieve and insert attendance records'
}
swagger = Swagger(app)

class EventHistory(db.Model):
    __tablename__ = 'eventhistory'

    HistoryPK = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserID = db.Column(db.Integer, nullable=False)
    EventID = db.Column(db.Integer, nullable=False)
    CheckInTiming = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.current_timestamp())

    def __init__(self, UserID, EventID):
        self.UserID = UserID
        self.EventID = EventID

    def json(self):
        return {
            "HistoryPK": self.HistoryPK,
            "UserID": self.UserID,
            "EventID": self.EventID,
            "CheckInTiming": self.CheckInTiming
        }

#View Event Attendance

@app.route("/attendance/events/<int:EventID>")
def event_attendance(EventID):
    """
    Get attendance of an event
    ---
    parameters:
        -   in: path
            name: EventID
            required: true
    responses:
        200:
            description: Return the attendance of all userIDs that attended
        404:
            description: Event not found

    """
    
    eventHistory = db.session.query(
        EventHistory.UserID).filter_by(
            EventID=EventID).all()
    
    if eventHistory:
        user_ids = [user_id for (user_id,) in eventHistory]
        return jsonify({
            "code": 200,
            "data": user_ids
        }), 200
    else:
        return jsonify({
            "code": 404,
            "message": "Event not found."
        }), 404

#Add User to Event Attendance

@app.route("/attendance/events/<string:EventID>", methods=['POST'])
def add_user_to_event_attendance(EventID):
    """
    Add user to Event Attendance
    ---
    parameters:
        - in: path
          name: EventID
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
            description: Ticket created successfully.
            content:
                application/json:
                    example:
                        code: 201
                        data:
                            EventID: "789"
                            UserID: "456"
                            CheckInTiming: "2024-03-06T10:00:00Z"
        400:
            description: Invalid request or missing parameters.
            content:
                application/json:
                    example:
                        code: 400
                        message: "User attendance already exists."
        500:
            description: An error occurred during event attendance creation.
            content:
                application/json:
                    example:
                        code: 500
                        message: "An error occurred during event attendance creation."
    """
    

    # Extracting UserID from request body
    data = request.get_json()
    UserID = data.get('UserID')
    
    # try:
    #     # Create event history
    #     event_history = EventHistory(UserID=UserID, EventID=EventID)
    #     db.session.add(event_history)
    #     db.session.commit()
        
    #     # Return success response
    #     return jsonify({
    #         "code": 201,
    #         "data": {
    #             "EventID": EventID,
    #             "UserID": UserID,
    #             "CheckInTiming": datetime.utcnow().isoformat() + 'Z'
    #         }
    #     }), 201

    # except Exception as e:
    #     # Log the error for debugging
    #     print("An error occurred:", e)

    #     # Rollback the session
    #     db.session.rollback()

    #     # Return error response
    #     return jsonify({
    #         "code": 500,
    #         "message": "An error occurred during event attendance creation."
    #     }), 500

    # Create event attendance
    event_history = EventHistory(EventID=EventID, UserID=UserID)

    try:
        db.session.add(event_history)
        db.session.commit()
    except:
        return jsonify({
            "code": 500,
            "message": "An error occurred during event attendance creation."
        }), 500

    # Return success response
    return jsonify({
        "code": 201,
        "data": {
            "EventID": EventID,
            "UserID": UserID,
            "CheckInTiming": datetime.utcnow()
        }
    }), 201


#View User Attendance

@app.route("/attendance/users/<int:UserID>")
def user_attendance(UserID):
    """
    Get attendance of a User
    ---
    parameters:
        -   in: path
            name: UserID
            required: true
    responses:
        200:
            description: Return the attendance of all events that user attended
        404:
            description: Event not found

    """
    
    eventHistory = db.session.query(
        EventHistory.EventID).filter_by(
            UserID=UserID).all()
    
    if eventHistory:
        event_ids = [event_id for (event_id,) in eventHistory]
        return jsonify({
            "code": 200,
            "data": event_ids
        }), 200
    else:
        return jsonify({
            "code": 404,
            "message": "User not found."
        }), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
