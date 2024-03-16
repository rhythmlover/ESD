import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dateutil import parser as date_parser
import json
import barcode
from barcode.writer import ImageWriter
import uuid

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost:3306/ticket'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}
db = SQLAlchemy(app)

def generate_barcode(barcode_data):
    try:
        code128 = barcode.get_barcode_class('code128')
        barcode_instance = code128(barcode_data, writer=ImageWriter())
        barcode_path = os.path.join('barcode_images', f'{barcode_data}.png')
        barcode_instance.save(barcode_path)
        return barcode_path
    except Exception as e:
        print("Error generating barcode:", str(e))
        return None

class Ticket(db.Model):
    __tablename__ = 'ticket'
    ticket_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(32), nullable=False)
    event_id = db.Column(db.Integer, nullable=False)
    ticket_type = db.Column(db.String(50), nullable=False)
    date_time = db.Column(db.DateTime, nullable=False)
    seat_location = db.Column(db.String(100))
    payment_id = db.Column(db.String(50))
    status = db.Column(db.String(20), default='Available')
    # bar_code = db.Column(db.Text)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    valid_till = db.Column(db.DateTime)

    def json(self):
        return {
            'ticket_id': self.ticket_id,
            'user_id': self.user_id,
            'event_id': self.event_id,
            'ticket_type': self.ticket_type,
            'date_time': self.date_time.isoformat(),
            'seat_location': self.seat_location,
            'payment_id': self.payment_id,
            'status': self.status,
            # 'bar_code': self.bar_code,
            'creation_date': self.creation_date.isoformat(),
            'valid_till': self.valid_till.isoformat() if self.valid_till else None
        }

@app.route("/tickets", methods=['GET'])
def get_all_tickets():
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

@app.route("/tickets/<int:ticket_id>", methods=['GET'])
def find_ticket_by_id(ticket_id):
    ticket = db.session.scalars(db.select(Ticket).filter_by(ticket_id=ticket_id).limit(1)).first()
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
            "data": {
                "ticket_id": ticket_id
            },
            "message": "Order not found."
        }
    ), 404

@app.route("/tickets", methods=['POST'])
def create_ticket():
    data = request.get_json()
    user_id = data.get('user_id', None)
    event_id = data.get('event_id', None)
    ticket_type = data.get('ticket_type', None)
    date_time = data.get('date_time', None)
    seat_location = data.get('seat_location', None)
    payment_id = data.get('payment_id', None)
    status = data.get('status', 'NEW')

    if date_time:
        date_time = date_parser.parse(date_time)

    # Create new ticket instance
    ticket = Ticket(
        user_id=user_id,
        event_id=event_id,
        ticket_type=ticket_type,
        date_time=date_time,
        seat_location=seat_location,
        payment_id=payment_id,
        status=status,
        # barcode generation is disabled
    )
    # barcode_path = generate_barcode(barcode_data)
    # if barcode_path:
    #     ticket.bar_code = barcode_path  # Ensure this matches the model field name
    # else:
    #     return jsonify({"code": 500, "message": "Failed to generate barcode."}), 500

    try:
        db.session.add(ticket)
        db.session.commit()
    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred while creating the ticket. " + str(e)
            }
        ), 500
    
    print(json.dumps(ticket.json(), default=str))
    print()

    return jsonify(
        {
            "code": 201,
            "data": ticket.json()
        }
    ), 201

@app.route("/order/<int:ticket_id>", methods=['PUT'])
def update_ticket(ticket_id):
    try:
        ticket = db.session.scalars(db.select(Ticket).filter_by(ticket_id=ticket_id).limit(1)).first()
        if not ticket:
            return jsonify(
                {
                    "code": 404,
                    "data": {
                        "ticket_id": ticket_id
                    },
                    "message": "Ticket not found."
                }
            ), 404

        update_fields = request.get_json()
        valid_fields = ['status', 'payment_id', 'user_id']

        for field in valid_fields:
            if field in update_fields:
                setattr(ticket, field, update_fields[field])
        
        db.session.commit()

        return jsonify(
            {
                "code": 200,
                "data": ticket.json()
            }
        ), 200

    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "data": {
                    "ticket_id": ticket_id
                },
                "message": "An error occurred while updating the ticket. " + str(e)
            }
        ), 500

if __name__ == '__main__':
    print("This is Flask for " + os.path.basename(__file__) + ": managing tickets ...")
    app.run(host='0.0.0.0', port=5001, debug=True)
