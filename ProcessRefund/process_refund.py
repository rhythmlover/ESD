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

refund_URL = "http://localhost:5001/refunds"
payment_URL = "http://localhost:5002/submit_refund"
email_URL = "http://localhost:5003/send_email"

# Using RabbitMQ as the message broker
error_URL = "http://localhost:5100/log/error"
refund_log_URL = "http://localhost:5100/log/activity"

exchangename = "refund_topic" # exchange name
exchangetype="topic" # use a 'topic' exchange to enable interaction

#create a connection and a channel to the broker to publish messages to activity_log, error queues
connection = amqp_connection.create_connection() 
channel = connection.channel()

#if the exchange is not yet created, exit the program
if not amqp_connection.check_exchange(channel, exchangename, exchangetype):
    print("\nCreate the 'Exchange' before running this microservice. \nExiting the program.")
    sys.exit(0)  # Exit with a success status

@app.route("/process_refund", methods=['POST'])
def process_refund():
    # Simple check of input format and data of the request are JSON
    if request.is_json:
        try:
            refund = request.get_json()
            print("\nReceived a refund in JSON:", refund)

            # do the actual work
            # 1. Send refund info {refund details: ticket_id, event_id, created time, status}

            # Check if user is requesting a refund or updating a refund
            if 'refund_status' in refund:
                result = updateRefund(refund)
                print('\n------------------------')
                print('\nresult: ', result)
                return jsonify(result), result["code"]
            else:
                result = createRefund(refund)
                print('\n------------------------')
                print('\nresult: ', result)
                return jsonify(result), result["code"]

        except Exception as e:
            # Unexpected error in code
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            ex_str = str(e) + " at " + str(exc_type) + ": " + fname + ": line " + str(exc_tb.tb_lineno)
            print(ex_str)

            return jsonify({
                "code": 500,
                "message": "process_refund.py internal error: " + ex_str
            }), 500

    # if reached here, not a JSON request.
    return jsonify({
        "code": 400,
        "message": "Invalid JSON input: " + str(request.get_data())
    }), 400


# Function to create a refund using the refund microservice
def createRefund(refund):
    # 2. Send the refund info {refund details: ticket_id, event_id, created time, status}
    # Invoke the refund microservice

    print('\n-----Invoking refund microservice-----')
    refund_result = invoke_http(refund_URL, method='POST', json=refund)
    print('refund_result:', refund_result)

    # Check the refund result; if a failure, send it to the error microservice.
    code = refund_result["code"]
    message = json.dumps(refund_result)

    if code not in range(200, 300):
        # Inform the error microservice
        #print('\n\n-----Invoking error microservice as refund fails-----')
        print('\n\n-----Publishing the (refund error) message with routing_key=refund.error-----')

        invoke_http(error_URL, method="POST", json=refund_result)
        channel.basic_publish(exchange=exchangename, routing_key="refund.error", 
            body=message, properties=pika.BasicProperties(delivery_mode = 2)) 
        # make message persistent within the matching queues until it is received by some receiver 
        # (the matching queues have to exist and be durable and bound to the exchange)

        # - reply from the invocation is not used;
        # continue even if this invocation fails        
        print("\Refund status ({:d}) published to the RabbitMQ Exchange:".format(
            code), refund_result)

        # Return error
        return {
            "code": 500,
            "data": {"refund_result": refund_result},
            "message": "Refund creation failure sent for error handling."
        }
    
    else:
        # Record new refund
        # record the refund log anyway
        print('\n\n-----Invoking refund_log microservice-----')
        print('\n\n-----Publishing the (refund info) message with routing_key=refund.info-----')        

        invoke_http(refund_log_URL, method="POST", json=refund_result)
        channel.basic_publish(exchange=exchangename, routing_key="refund.info", 
            body=message)
        
        # Return success FOR NOW
        return {
            "code": 201,
            "data": {"refund_result": refund_result},
            "message": "Refund request created successfully."
        }
        
    print("\Refund published to RabbitMQ Exchange.\n")
    # - reply from the invocation is not used;
    # continue even if this invocation fails
    
# Function to update a refund using the refund microservice
def updateRefund(refund):
    # Send new refund to refund to update refund status
    # Invoke the refund microservice
    print('\n\n-----Invoking refund microservice-----')
    
    update_refund_result = invoke_http(refund_URL, method="PUT", json=refund)
    print("refund_result:", update_refund_result, '\n')

    #Check the update refund result; if failure, send to error microservice
    code = update_refund_result['code']
    if code not in range(200, 300):
        # Inform the error microservice
        print('\n\n-----Invoking error microservice as shipping fails-----')
        print('\n\n-----Publishing the (refund update error) message with routing_key=refund.error-----')

        invoke_http(error_URL, method="POST", json=update_refund_result)
        message = json.dumps(update_refund_result)
        channel.basic_publish(exchange=exchangename, routing_key="refund.error", 
            body=message, properties=pika.BasicProperties(delivery_mode = 2))

        print("\nUpdate refund status ({:d}) published to the RabbitMQ Exchange:".format(code), update_refund_result)

        # 7. Return error
        return {
            "code": 400,
            "data": {
                "update_refund_result": update_refund_result
            },
            "message": "There was an error in updating refund result"
        }
    
    # If update refund was successful:
    # Checking refund status to decide next actions
    refund_status = update_refund_result['refund_status']

    if refund_status == "approved" or refund_status == "Approved":
        pass
    elif refund_status == "rejected" or refund_status == "Rejected":
        # 2. Send the updated refund result {refund details: ticket_id, event_id, created time, status}
        # Invoke the email microservice

        print('\n-----Invoking email microservice-----')
        update_refund_result = invoke_http(email_URL, method='POST', json=update_refund_result)
        print('update_refund_result:', update_refund_result)

        # Check the email result; if a failure, send it to the error microservice.
        code = update_refund_result["code"]
        message = json.dumps(update_refund_result)

        if code not in range(200, 300):
            # Inform the error microservice
            print('\n\n-----Invoking error microservice as send email fails-----')
            print('\n\n-----Publishing the (email error) message with routing_key=email.error-----')

            invoke_http(error_URL, method="POST", json=update_refund_result)
            channel.basic_publish(exchange=exchangename, routing_key="email.error", 
                body=message, properties=pika.BasicProperties(delivery_mode = 2)) 
            # make message persistent within the matching queues until it is received by some receiver 
            # (the matching queues have to exist and be durable and bound to the exchange)

            # - reply from the invocation is not used;
            # continue even if this invocation fails        
            print("\Email status ({:d}) published to the RabbitMQ Exchange:".format(
                code), update_refund_result)

            # Return error
            return {
                "code": 500,
                "data": {"refund_result": update_refund_result},
                "message": "Refund creation failure sent for error handling."
            }
        
        else:
            # Record new email
            # record the refund log anyway
            print('\n\n-----Invoking refund_log microservice-----')
            print('\n\n-----Publishing the (refund info) message with routing_key=refund.info-----')        

            invoke_http(refund_log_URL, method="POST", json=update_refund_result)            
            channel.basic_publish(exchange=exchangename, routing_key="email.info", 
                body=message)
            
        print("\Refund published to RabbitMQ Exchange.\n")
        # - reply from the invocation is not used;
        # continue even if this invocation fails



# Execute this program if it is run as a main script (not by 'import')
if __name__ == "__main__":
    print("This is flask " + os.path.basename(__file__) + " for processing a refund...")
    app.run(host="0.0.0.0", port=5100, debug=True)
    # Notes for the parameters: 
    # - debug=True will reload the program automatically if a change is detected;
    #   -- it in fact starts two instances of the same flask program, and uses one of the instances to monitor the program changes;
    # - host="0.0.0.0" allows the flask program to accept requests sent from any IP/host (in addition to localhost),
    #   -- i.e., it gives permissions to hosts with any IP to access the flask program,
    #   -- as long as the hosts can already reach the machine running the flask program along the network;
    #   -- it doesn't mean to use http://0.0.0.0 to access the flask program.
