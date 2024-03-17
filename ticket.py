import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost:3306/ticket'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}
db = SQLAlchemy(app)

# Database Models
class Ticket(db.Model):
    __tablename__ = 'ticket'
    ticket_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(32), nullable=False)
    event_id = db.Column(db.Integer, nullable=False)  # Changed to Integer for consistency
    ticket_type = db.Column(db.String(50), nullable=False)
    date_time = db.Column(db.DateTime, nullable=False)
    seat_location = db.Column(db.String(100))
    payment_id = db.Column(db.String(50))
    status = db.Column(db.String(20), default='Available')
    qr_code = db.Column(db.Text)
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
            'qr_code': self.qr_code,
            'creation_date': self.creation_date.isoformat(),
            'valid_till': self.valid_till.isoformat() if self.valid_till else None
        }

class Ticket_Item(db.Model):
    __tablename__ = 'ticket_item'
    ticket_item_id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.ticket_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    event_id = db.Column(db.Integer, nullable=False)  # Changed to Integer for consistency
    quantity = db.Column(db.Integer, nullable=False)

    def json(self):
        return {'ticket_item_id': self.ticket_item_id, 'ticket_id': self.ticket_id, 'event_id': self.event_id, 'quantity': self.quantity}

# Routes
@app.route("/tickets", methods=['GET'])
def get_all_tickets():
    tickets = Ticket.query.all()
    if tickets:
        return jsonify({"code": 200, "data": [ticket.json() for ticket in tickets]})
    return jsonify({"code": 404, "message": "There are no tickets."}), 404

@app.route("/tickets/<int:ticket_id>", methods=['GET'])
def find_ticket_by_id(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if ticket:
        return jsonify({"code": 200, "data": ticket.json()})
    return jsonify({"code": 404, "message": "Ticket not found."}), 404

@app.route("/tickets", methods=['POST'])
def create_ticket():
    data = request.json
    if not data:
        return jsonify({"code": 400, "message": "Request data is missing."}), 400

    user_id = data.get('user_id')
    ticket_type = data.get('ticket_type')
    date_time = data.get('date_time')

    if not all([user_id, ticket_type, date_time]):
        return jsonify({"code": 400, "message": "User ID, ticket type, and date time are required."}), 400

    try:
        date_time = datetime.fromisoformat(date_time)
    except ValueError:
        return jsonify({"code": 400, "message": "Invalid date and time format."}), 400

    # Process creating the ticket
    # (Your implementation here)

@app.route("/tickets/<int:ticket_id>", methods=['PUT'])
def update_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return jsonify({"code": 404, "message": "Ticket not found."}), 404

    data = request.json
    if not data:
        return jsonify({"code": 400, "message": "Request data is missing."}), 400

    status = data.get('status')
    if status is not None:
        ticket.status = status

    try:
        db.session.commit()
        return jsonify({"code": 200, "data": ticket.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"An error occurred while updating the ticket: {str(e)}"}), 500

if __name__ == '__main__':
    print("This is Flask for " + os.path.basename(__file__) + ": managing tickets ...")
    app.run(host='0.0.0.0', port=5001, debug=True)
