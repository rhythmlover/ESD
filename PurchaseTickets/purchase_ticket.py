from flask import Flask, request, jsonify
from flask_cors import CORS
import os, sys
import requests
from invokes import invoke_http
import pika
import json
import amqp_connection

app = Flask(__name__)
CORS(app)

# Replace these URLs with the actual URLs of your microservices
ticket_URL = "http://localhost:5001/ticket"
payment_URL = "http://localhost:5002/payment"
email_URL = "http://localhost:5003/email"
user_URL = "http://localhost:5004/user"

exchangename = "ticket_topic"
exchangetype = "topic"

connection = amqp_connection.create_connection() 
channel = connection.channel()

if not amqp_connection.check_exchange(channel, exchangename, exchangetype):
    print("\nCreate the 'Exchange' before running this microservice. \nExiting the program.")
    sys.exit(0)

@app.route("/purchase_ticket", methods=['POST'])
def purchase_ticket():
    if request.is_json:
        try:
            ticket = request.get_json()
            print("\nReceived a ticket purchase request:", ticket)


            user_id = ticket.get('user_id')
            user_data = get_user_data(user_id)
            if not user_data:
                return jsonify({"code": 404, "message": "User not found."}), 404
            
            # Invoke ticket service to create ticket
            ticket_result = invoke_http(ticket_URL, method='POST', json=ticket)

            # Check if ticket creation was successful
            if ticket_result["code"] != 201:
                return jsonify(ticket_result), ticket_result["code"]

            # Proceed to payment
            payment_data = {
                "user_id": ticket.get("user_id"),
                "ticket_id": ticket_result["data"]["ticket_id"],
                # Include other payment details here if needed
            }
            payment_result = invoke_http(payment_URL, method='POST', json=payment_data)

            # Check if payment was successful
            if payment_result["code"] != 200:
                return jsonify(payment_result), payment_result["code"]

            # Proceed to notification
            email_data = {
                "email": ticket.get("email"),  # Assuming email is part of ticket data
                "message": "Ticket purchased successfully!",
                "barcode_image": ticket_result["data"]["barcode_image"]  # Assuming barcode image is returned from ticket creation
                # Add other relevant data for notification here
            }
            email_result = invoke_http(email_URL, method='POST', json=email_data)

            # Return final result
            return jsonify(email_result), email_result["code"]

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            ex_str = str(e) + " at " + str(exc_type) + ": " + fname + ": line " + str(exc_tb.tb_lineno)
            print(ex_str)

            return jsonify({
                "code": 500,
                "message": "purchase_ticket.py internal error: " + ex_str
            }), 500

    return jsonify({
        "code": 400,
        "message": "Invalid JSON input: " + str(request.get_data())
    }), 400

def get_user_data(user_id):
    # Call the user microservice to retrieve user data
    user_response = requests.get(f"{user_URL}/{user_id}")
    if user_response.status_code == 200:
        return user_response.json()
    else:
        return None

def process_purchase_ticket(ticket):
    print('\n-----Invoking ticket microservice-----')
    ticket_result = invoke_http(ticket_URL, method='POST', json=ticket)
    print('ticket_result:', ticket_result)

    code = ticket_result["code"]
    message = json.dumps(ticket_result)

    if code not in range(200, 300):
        print('\n\n-----Publishing the (ticket error) message with routing_key=ticket.error-----')
        channel.basic_publish(exchange=exchangename, routing_key="ticket.error", 
            body=message, properties=pika.BasicProperties(delivery_mode = 2))

        print("\nTicket purchase status ({:d}) published to the RabbitMQ Exchange:".format(
            code), ticket_result)

        return {
            "code": 400,
            "data": {"ticket_result": ticket_result},
            "message": "Ticket purchase failure sent for error handling."
        }
    
    return {
        "code": 201,
        "data": {
            "ticket_result": ticket_result,
        }
    }

if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) + " for purchasing a ticket...")
    app.run(host="0.0.0.0", port=5100, debug=True)