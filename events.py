#import Flask, request, jsonify from library flask
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

#initialise 
app = Flask(__name__)

#The SQLAlchemy Database URI format is: dialect+driver://username:password@host:port/database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/event'
#Disable modification tracking as it requires extra memory and is not needed
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#Initialize a connection to the database and keep this in the db variable
db = SQLAlchemy(app)

#We create a new class event, which inherits from a basic database model, provided by SQLAlchemy.
class event(db.Model):
    #Specify the table name as event 
    __tablename__ = 'event'

    #define data column name, type and if it is nullable (able to not enter input)
    #add (number) after db.String to limit the length
    event_id = db.Column(db.String, primary_key=True) 
    event_name = db.Column(db.String(64), nullable=False)
    event_price = db.Column(db.Float(precision=2), nullable=False)
    date = db.Column(db.DateTime, nullable=False) #may need to check datatype for this

    #Specify the properties of a event when it is created
    def __init__(self, event_id, title, price):
        self.event_id = event_id
        self.title = title
        self.price = price

    #Represent our event object as a JSON string
    def json(self):
        return {"event_id": self.event_id, "title": self.title, "price": self.price}



#Use Flask's app.route decorator to map the URL route /event to the function get_all
#To call this function, the URL to use is for GET
@app.route("/event")
def get_all():
    #SQLAlchemy provides a session.scalars attribute to retrieve all records from the book table using db.select(Book).all(); this returns a list, which we assign to booklist
    eventlist = db.session.scalars(db.select(event)).all()

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

#Use Flask's app.route decorator to map the URL route /event/<string:event_id> to the function find_by_event_id
#To call this function, the URL to use is for GET
@app.route("/event/<string:event_id>")
def find_by_eventid(event_id):
    #Retrieve only the event with the event_id specified in the path variable, similar to the WHERE clause in a SQL SELECT expression
    event = db.session.scalars(
    	db.select(event).filter_by(event_id = event_id).
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


#Use Flask's app.route decorator to map the URL route /event/<string:event_id> to the function find_by_event_id
#To call this function, the URL to use is for POST
@app.route("/event/<string:event_id>", methods=['POST'])
def create_event(event_id):
    #check if the event already exists in the table
    if (db.session.scalars(
    	db.select(event).filter_by(event_id = event_id).
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
                "message": "event already exists."
            }
        ), 400
    
    #Details of the event have to be sent in the body of the request in JSON format
    data = request.get_json()
    #Then we create an instance of a event using the event_id and the attributes sent in the request (**data)
    #** is a common idiom to allow an arbitrary number of arguments to a function
    event = event(event_id, **data)

    try:
        #To add the event to the table and commit the changes, we use the db.session object (provided by SQLAlchemy) 
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

#Because, we have added the following, we can run it as above instead of python -m flask run 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)