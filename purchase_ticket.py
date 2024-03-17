from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import json
import amqp_connection

app = Flask(__name__)
CORS(app)

# Replace these URLs with the actual URLs of your microservices
ticket_URL = "http://localhost:5001/tickets"
shipping_record_URL = "http://localhost:5002/shipping_record"

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

            result = process_purchase_ticket(ticket)
            print('\n------------------------')
            print('\nresult: ', result)
            return jsonify(result), result["code"]

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
            "code": 500,
            "data": {"ticket_result": ticket_result},
            "message": "Ticket purchase failure sent for error handling."
        }

    else:
        print('\n\n-----Publishing the (ticket info) message with routing_key=ticket.info-----')
        channel.basic_publish(exchange=exchangename, routing_key="ticket.info", 
            body=message)

    print("\nTicket purchase published to RabbitMQ Exchange.\n")

    print('\n\n-----Invoking shipping_record microservice-----')    
    shipping_result = invoke_http(
        shipping_record_URL, method="POST", json=ticket_result['data'])
    print("shipping_result:", shipping_result, '\n')

    code = shipping_result["code"]
    if code not in range(200, 300):
        print('\n\n-----Publishing the (shipping error) message with routing_key=shipping.error-----')
        message = json.dumps(shipping_result)
        channel.basic_publish(exchange=exchangename, routing_key="shipping.error", 
            body=message, properties=pika.BasicProperties(delivery_mode = 2))

        print("\nShipping status ({:d}) published to the RabbitMQ Exchange:".format(
            code), shipping_result)

        return {
            "code": 400,
            "data": {
                "ticket_result": ticket_result,
                "shipping_result": shipping_result
            },
            "message": "Simulated shipping record error sent for error handling."
        }

    return {
        "code": 201,
        "data": {
            "ticket_result": ticket_result,
            "shipping_result": shipping_result
        }
    }


if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) + " for purchasing a ticket...")
    app.run(host="0.0.0.0", port=5100, debug=True)