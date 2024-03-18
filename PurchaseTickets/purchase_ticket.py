from flask import Flask, request, jsonify
from flask_cors import CORS
import os, sys
from invokes import invoke_http
import json
import amqp_connection

app = Flask(__name__)
CORS(app)

ticket_URL = "http://localhost:5001/tickets"
payment_URL = "http://localhost:5002/process_payment"
email_URL = "http://localhost:5003/sendEmail"
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
            ticket_request = request.get_json()
            ticket_request = request.get_json()
            user_id = ticket_request.get('user_id')
            event_id = ticket_request.get('event_id')
            ticket_type = ticket_request.get('ticket_type')
            date_time = ticket_request.get('date_time')
            seat_location = ticket_request.get('seat_location')

            # Step 1: Fetch user details
            user_response = get_user_data(user_id)
            if not user_response:
                return jsonify({"code": 404, "message": "User not found."}), 404

            # Step 2: Create Ticket
            ticket_response = invoke_http(ticket_URL, method='POST', json=ticket_request)
            if ticket_response["code"] not in range(200, 300):
                return jsonify(ticket_response), ticket_response["code"]

            # Step 3: Process Payment
            payment_response = invoke_http(payment_URL, method='POST', json={
                "user_id": user_id,
                "ticket_id": ticket_response["data"]["ticket_id"],
                "amount": ticket_request.get('data', {}).get('amount'),
                "currency": "usd",
                "payment_method_id": "pm_1OuxTr2LHSKllIVV0edx7rsn" 
            })
            if payment_response["code"] == 200:
                payment_id = payment_response["data"]["payment_id"]

                ticket_update_data = {
                    "payment_id": payment_id
                }
                update_response = invoke_http(f"{ticket_URL}/order/{ticket_response['data']['ticket_id']}", method='PUT', json=ticket_update_data)
                
                if update_response["code"] not in range(200, 300):
                    return jsonify(update_response), update_response["code"]
            else:
                return jsonify(payment_response), payment_response["code"]    

            # Step 5: Send Notification
            email_response = invoke_http(email_URL, method='POST', json={
                "email": user_response["email"],
                "message": "Your ticket has been successfully purchased.",
                "ticket_details": ticket_response["data"],
                "payment_details": payment_response["data"]
            })
            if email_response["code"] not in range(200, 300):
                return jsonify(email_response), email_response["code"]
            
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
    user_response = invoke_http(f"{user_URL}/{user_id}", method='GET')
    if user_response.get("code") == 200:
        return user_response.get("data")
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