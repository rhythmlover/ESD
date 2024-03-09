from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:3306/ticket'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Ticket(db.Model):
    __tablename__ = 'ticket'

    ticket_id = db.Column(db.String(13), primary_key=True)
    event_name = db.Column(db.String(64), nullable=False)
    price = db.Column(db.Float(precision=2), nullable=False)
    availability = db.Column(db.Integer)

    def __init__(self, ticket_id, event_name, price, availability):
        self.ticket_id = ticket_id
        self.event_name = event_name
        self.price = price
        self.availability = availability

    def json(self):
        return {"ticket_id": self.ticket_id, "event_name": self.event_name, "price": self.price, "availability": self.availability}

@app.route("/ticket")
def get_all():
    ticketlist = db.session.scalars(db.select(Ticket)).all()

    if len(ticketlist):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "tickets": [ticket.json() for ticket in ticketlist]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no tickets."
        }
    ), 404
   
@app.route("/ticket/<string:ticket_id>")
def find_by_ticket_id(ticket_id):
    ticket = db.session.scalars(
        db.select(Ticket).filter_by(ticket_id=ticket_id).
        limit(1)
).first()

    if ticket:
        return jsonify(
            {
                "code": 200,
                "data": ticket.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "Ticket not found."
        }
    ), 404

@app.route("/ticket/<string:ticket_id>", methods=['POST'])
def create_ticket(ticket_id):
    if (db.session.scalars(
        db.select(Ticket).filter_by(ticket_id=ticket_id).
        limit(1)
).first()
):
        return jsonify(
            {
                "code": 400,
                "data": {
                    "ticket_id": ticket_id
                },
                "message": "Ticket already exists."
            }
        ), 400

    data = request.get_json()
    ticket = Ticket(ticket_id, **data)

    try:
        db.session.add(ticket)
        db.session.commit()
    except:
        return jsonify(
            {
                "code": 500,
                "data": {
                    "ticket_id": ticket_id
                },
                "message": "An error occurred creating the ticket."
            }
        ), 500

    return jsonify(
        {
            "code": 201,
            "data": ticket.json()
        }
    ), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)


