#!/usr/bin/env python3
# The above shebang (#!) operator tells Unix-like environments
# to run this file as a python3 script

import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:3306/refund'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)


class Refund(db.Model):
    __tablename__ = 'refund'

    refund_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(32), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    modified = db.Column(db.DateTime, nullable=False,
                         default=datetime.now, onupdate=datetime.now)

    def json(self):
        dto = {
            'refund_id': self.refund_id,
            'customer_id': self.customer_id,
            'status': self.status,
            'created': self.created,
            'modified': self.modified
        }

        dto['refund_item'] = []
        for oi in self.refund_item:
            dto['refund_item'].append(oi.json())

        return dto


class Refund_Item(db.Model):
    __tablename__ = 'refund_item'

    item_id = db.Column(db.Integer, primary_key=True)
    refund_id = db.Column(db.ForeignKey(
        'refund.refund_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)

    book_id = db.Column(db.String(13), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    # refund_id = db.Column(db.String(36), db.ForeignKey('refund.refund_id'), nullable=False)
    # refund = db.relationship('Refund', backref='refund_item')
    refund = db.relationship(
        'Refund', primaryjoin='Refund_Item.refund_id == Refund.refund_id', backref='refund_item')

    def json(self):
        return {'item_id': self.item_id, 'book_id': self.book_id, 'quantity': self.quantity, 'refund_id': self.refund_id}


@app.route("/refund")
def get_all():
    refundlist = db.session.scalars(db.select(Refund)).all()
    if len(refundlist):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "refunds": [refund.json() for refund in refundlist]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no refunds."
        }
    ), 404


@app.route("/refund/<string:refund_id>")
def find_by_refund_id(refund_id):
    refund = db.session.scalars(
        db.select(Refund).filter_by(refund_id=refund_id).limit(1)).first()
    if refund:
        return jsonify(
            {
                "code": 200,
                "data": refund.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "data": {
                "refund_id": refund_id
            },
            "message": "Refund not found."
        }
    ), 404


@app.route("/refund", methods=['POST'])
def create_refund():
    customer_id = request.json.get('customer_id', None)
    refund = Refund(customer_id=customer_id, status='NEW')

    cart_item = request.json.get('cart_item')
    for item in cart_item:
        refund.refund_item.append(Refund_Item(
            book_id=item['book_id'], quantity=item['quantity']))

    try:
        db.session.add(refund)
        db.session.commit()
    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred while creating the refund. " + str(e)
            }
        ), 500

    return jsonify(
        {
            "code": 201,
            "data": refund.json()
        }
    ), 201


@app.route("/refund/<string:refund_id>", methods=['PUT'])
def update_refund(refund_id):
    try:
        refund = db.session.scalars(
        db.select(Refund).filter_by(refund_id=refund_id).
        limit(1)).first()
        if not refund:
            return jsonify(
                {
                    "code": 404,
                    "data": {
                        "refund_id": refund_id
                    },
                    "message": "Refund not found."
                }
            ), 404

        # update status
        data = request.get_json()
        if data['status']:
            refund.status = data['status']
            db.session.commit()
            return jsonify(
                {
                    "code": 200,
                    "data": refund.json()
                }
            ), 200
    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "data": {
                    "refund_id": refund_id
                },
                "message": "An error occurred while updating the refund. " + str(e)
            }
        ), 500


if __name__ == '__main__':
    print("This is flask for " + os.path.basename(__file__) + ": manage refunds ...")
    app.run(host='0.0.0.0', port=5002, debug=True)
