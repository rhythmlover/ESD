from flask import Flask, request, jsonify
from flask_cors import CORS
from invokes import invoke_http

import os, sys
import pika
import json
import amqp_connection

app = Flask(__name__)
CORS(app)

refund_URL = "http://localhost:5001/refunds"
payment_URL = "http://localhost:5002/submit_refund"
email_URL = "http://localhost:5003/send_email"
user_URL = "http://localhost:5004/users"
ticket_URL = "http://localhost:5005/tickets"

# Using RabbitMQ as the message broker
error_URL = "http://localhost:5100/log/error"
activity_log_URL = "http://localhost:5100/log/activity"

exchangename = "refund_topic" # exchange name
exchangetype = "topic" # use a 'topic' exchange to enable interaction

#create a connection and a channel to the broker to publish messages to activity_log, error queues
connection = amqp_connection.create_connection() 
channel = connection.channel()

#if the exchange is not yet created, exit the program
if not amqp_connection.check_exchange(channel, exchangename, exchangetype):
    print("\nCreate the 'Exchange' before running this microservice. \nExiting the program.")
    sys.exit(0)

@app.route("/process_refund", methods=['POST'])
def process_refund():
    if request.is_json:
        try:
            body_request = request.get_json()
            print("\nReceived a refund in JSON:", body_request)

            # Fetch user details
            user_id = body_request.get('user_id')
            user_response = get_user_data(user_id)
            if not user_response:
                return jsonify({"code": 404, "message": "User not found."}), 404
            
            # Check if the refund is an admin processing refund or a user creating refund
            if body_request['type'] == "process":
                result = processRefund(body_request, user_response)
                print('\n------------------------')
                print('\nresult: ', result)
                return jsonify(result), result["code"]
            elif body_request['type'] == "create":
                result = createRefund(body_request, user_response)
                print('\n------------------------')
                print('\nresult: ', result)
                return jsonify(result), result["code"]
            else:
                return jsonify({
                    "code": 400,
                    "message": "Invalid type. Must be process or create."
                }), 400

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
def createRefund(refund, user_response):
    print('\n-----Invoking Refund Microservice-----')
    refund_result = invoke_http(refund_URL, method='POST', json=refund)
    print('creating_refund_result:', refund_result)
    refund_message = json.dumps(refund_result)

    # Check the refund result; if a failure, send it to the error microservice.
    code = refund_result["code"]
    
    if code not in range(200, 300):
        # Inform the error microservice
        print('\n-----Publishing the (refund error) message with routing_key=refund.error-----')

        invoke_http(error_URL, method="POST", json=refund_result)
        channel.basic_publish(exchange=exchangename, routing_key="refund.error", 
            body=refund_message, properties=pika.BasicProperties(delivery_mode = 2)) 
        # make message persistent within the matching queues until it is received by some receiver 
        # (the matching queues have to exist and be durable and bound to the exchange)
      
        print("\nRefund status ({:d}) published to the RabbitMQ Exchange:".format(
            code), refund_result)

        print('\n-----Invoking Refund Microservice Failed-----')
        # Return error
        return {
            "code": 500,
            "message": "Refund creation failure sent for error handling."
        }

    print('\n-----Invoking refund_log microservice-----')
    print('\n-----Publishing the (refund info) message with routing_key=refund.info-----')        
    invoke_http(refund_log_URL, method="POST", json=refund_result)
    channel.basic_publish(exchange=exchangename, routing_key="refund.info", 
        body=refund_message)
    print("\nRefund published to RabbitMQ Exchange.")

    print('\n-----Successfully Invoked Refund Microservice-----')

    message = f"""
            <html>
                <body>
                    <h1>Refund Request Created</h1>
                    <p>We have received your request for the refund of your ticket.</p>
                    <ul>
                        <li><strong>User ID:</strong> {user_response["user_id"]}</li>
                        <li><strong>Event ID:</strong> {refund['event_id']}</li>
                        <li><strong>Ticket ID:</strong> {refund['ticket_id']}</li>
                        <li><strong>Refund Status:</strong> Pending </li>
                    </ul>
                    <p>Best regards,<br>Ticketmaster</p>
                </body>
            </html>
            """

    print('\n-----Invoking email microservice-----')
    email_refund_result = invoke_http(email_URL, method='POST', json={
        "to_email": user_response["email"],
        "html_content": message
    })
    print("email_refund_result:", email_refund_result)
    email_refund_message = json.dumps(email_refund_result)

    code = email_refund_result["code"]
    
    if code not in range(200, 300):
        # Inform the error microservice
        print('\n-----Invoking error microservice as send email fails-----')
        print('\n-----Publishing the (email error) message with routing_key=email.error-----')

        invoke_http(error_URL, method="POST", json=email_refund_message)
        channel.basic_publish(exchange=exchangename, routing_key="email.error", 
            body=email_refund_message, properties=pika.BasicProperties(delivery_mode = 2)) 
        # make message persistent within the matching queues until it is received by some receiver 
        # (the matching queues have to exist and be durable and bound to the exchange)

        # - reply from the invocation is not used;
        # continue even if this invocation fails        
        print("\nEmail status ({:d}) published to the RabbitMQ Exchange:".format(
            code), email_refund_message)
            
        return {
            "code": 500,
            "message": "Email failure sent for error handling."
        }
    
    print('\n-----Invoking refund_log microservice-----')
    print('\n-----Publishing the (email info) message with routing_key=email.info-----')
    invoke_http(refund_log_URL, method="POST", json=email_refund_result)
    channel.basic_publish(exchange=exchangename, routing_key="email.info",
        body=email_refund_message)
    print("\nEmail published to RabbitMQ Exchange.")

    print('\n-----Successfully Invoked Email Microservice-----')  

    print('\n-----Successfully Invoked Refund Microservice-----')  
    return {
        "code": 201,
        "message": "Refund request created successfully."
    }
    
# Function to process a refund using the refund microservice
def processRefund(refund, user_response):
    # Check the refund decision of the admin
    if refund['decision'] == "approve":
        print('\n-----Invoking ticket microservice-----')
        ticket_response = invoke_http(f"{ticket_URL}/{refund['ticket_id']}", method='GET')
        print('ticket_response:', ticket_response)
        ticket_message = json.dumps(ticket_response)

        code = ticket_response["code"]

        if code not in range(200, 300):
            # Inform the error microservice
            print('\n-----Invoking error microservice as ticket details fails-----')
            print('\n-----Publishing the (ticket error) message with routing_key=ticket.error-----')

            invoke_http(error_URL, method="POST", json=ticket_response)
            channel.basic_publish(exchange=exchangename, routing_key="ticket.error", 
                body=ticket_message, properties=pika.BasicProperties(delivery_mode = 2)) 
            # make message persistent within the matching queues until it is received by some receiver 
            # (the matching queues have to exist and be durable and bound to the exchange)
      
            print("\nTicket status ({:d}) published to the RabbitMQ Exchange:".format(
                code), ticket_response)

            # Return error
            return {
                "code": 500,
                "message": "Ticket details failure sent for error handling."
            }
        
        print('\n-----Invoking refund_log microservice-----')
        print('\n-----Publishing the (ticket info) message with routing_key=ticket.info-----')        
        invoke_http(refund_log_URL, method="POST", json=ticket_response)
        channel.basic_publish(exchange=exchangename, routing_key="ticket.info",
            body=ticket_message)
        print("\Ticket published to RabbitMQ Exchange.")

        print('\n-----Successfully Invoked Ticket Microservice-----')

        print('\n-----Invoking payment microservice-----')
        payment_result = invoke_http(payment_URL, method='POST', json={'charge_id': ticket_response["data"]["charge_id"]})
        print('executing_refund_result:', payment_result)
        payment_message = json.dumps(payment_result)

        code = payment_result["code"]
    
        if code not in range(200, 300):
            # Inform the error microservice
            print('\n-----Invoking error microservice as payment of refund fails-----')
            print('\n-----Publishing the (payment error) message with routing_key=payment.error-----')

            invoke_http(error_URL, method="POST", json=payment_result)
            channel.basic_publish(exchange=exchangename, routing_key="payment.error", 
                body=payment_message, properties=pika.BasicProperties(delivery_mode = 2)) 
            # make message persistent within the matching queues until it is received by some receiver 
            # (the matching queues have to exist and be durable and bound to the exchange)
      
            print("\nPayment status ({:d}) published to the RabbitMQ Exchange:".format(
                code), payment_result)

            # Return error
            return {
                "code": 500,
                "message": "Refund payment failure sent for error handling."
            }
        
        print('\n-----Invoking refund_log microservice-----')
        print('\n-----Publishing the (payment info) message with routing_key=payment.info-----')        
        invoke_http(refund_log_URL, method="POST", json=payment_result)
        channel.basic_publish(exchange=exchangename, routing_key="payment.info",
            body=payment_message)
        print("\Payment published to RabbitMQ Exchange.")

        print('\n-----Successfully Invoked Payment Microservice-----')
        
        print('\n-----Invoking Refund Microservice-----')
        update_refund_result = invoke_http(refund_URL, method="PUT", json={
            "event_id": refund['event_id'],
            "ticket_id": refund['ticket_id'],
            "refund_status": "approved"
        })
        print("update_refund_result:", update_refund_result)
        update_refund_message = json.dumps(update_refund_result)

        code = update_refund_result["code"]

        if code not in range(200, 300):
            # Inform the error microservice
            print('\n-----Invoking error microservice as updating of refund details fails-----')
            print('\n-----Publishing the (update refund error) message with routing_key=refund.error-----')

            invoke_http(error_URL, method="POST", json=update_refund_result)
            channel.basic_publish(exchange=exchangename, routing_key="refund.error", 
                body=update_refund_message, properties=pika.BasicProperties(delivery_mode = 2)) 
            # make message persistent within the matching queues until it is received by some receiver 
            # (the matching queues have to exist and be durable and bound to the exchange)
      
            print("\nRefund status ({:d}) published to the RabbitMQ Exchange:".format(
                code), update_refund_result)

            # Return error
            return {
                "code": 500,
                "message": "Updating refund details failed sent for error handling."
            }
        
        print('\n-----Invoking refund_log microservice-----')
        print('\n-----Publishing the (update refund info) message with routing_key=refund.info-----')        
        invoke_http(refund_log_URL, method="POST", json=update_refund_result)
        channel.basic_publish(exchange=exchangename, routing_key="refund.info", 
            body=update_refund_message)
        print("\nRefund published to RabbitMQ Exchange.")

        print("\n-----Successfully Invoked Refund Microservice-----")

        message = f"""
            <html>
                <body>
                    <h1>Refund Confirmation</h1>
                    <p>We have approved your refund request of your ticket and a refund have been successful issued.</p>
                    <ul>
                        <li><strong>User ID:</strong> {user_response["user_id"]}</li>
                        <li><strong>Event ID:</strong> {refund['event_id']}</li>
                        <li><strong>Ticket ID:</strong> {refund['ticket_id']}</li>
                        <li><strong>Refund Status:</strong> Approved </li>
                    </ul>
                    <p>Best regards,<br>Ticketmaster</p>
                </body>
            </html>
            """

        print('\n-----Invoking email microservice-----')
        email_refund_result = invoke_http(email_URL, method='POST', json={
            "to_email": user_response["email"],
            "html_content": message
        })
        print("email_refund_result:", email_refund_result)
        email_refund_message = json.dumps(email_refund_result)

        code = email_refund_result["code"]
        
        if code not in range(200, 300):
            # Inform the error microservice
            print('\n-----Invoking error microservice as send email fails-----')
            print('\n-----Publishing the (email error) message with routing_key=email.error-----')

            invoke_http(error_URL, method="POST", json=email_refund_result)
            channel.basic_publish(exchange=exchangename, routing_key="email.error", 
                body=email_refund_message, properties=pika.BasicProperties(delivery_mode = 2)) 
            # make message persistent within the matching queues until it is received by some receiver 
            # (the matching queues have to exist and be durable and bound to the exchange)

            # - reply from the invocation is not used;
            # continue even if this invocation fails        
            print("\nEmail status ({:d}) published to the RabbitMQ Exchange:".format(
                code), email_refund_result)
             
            return {
                "code": 500,
                "message": "Email failure sent for error handling."
            }
        
        print('\n-----Invoking refund_log microservice-----')
        print('\n-----Publishing the (email info) message with routing_key=email.info-----')        
        invoke_http(refund_log_URL, method="POST", json=email_refund_result)
        channel.basic_publish(exchange=exchangename, routing_key="email.info", 
            body=email_refund_message)
        print("\Email published to RabbitMQ Exchange.")

        print('\n-----Successfully Invoked Email microservice-----')  

        print('\n-----Successfully Invoked Payment Microservice-----')
        return {
            "code": 201,
            "message": "Refund request approved and issued."
        }
    
    elif refund['decision'] == "reject":
        # Update the refund status to rejected
        print('\n-----Invoking Refund Microservice-----')
        update_refund_result = invoke_http(refund_URL, method="PUT", json={
            "event_id": refund['event_id'],
            "ticket_id": refund['ticket_id'],
            "refund_status": "rejected"
        })
        print("update_refund_result:", update_refund_result)
        update_refund_message = json.dumps(update_refund_result)

        code = update_refund_result["code"]

        if code not in range(200, 300):
            # Inform the error microservice
            print('\n-----Invoking error microservice as updating of refund details fails-----')
            print('\n-----Publishing the (update refund error) message with routing_key=refund.error-----')

            invoke_http(error_URL, method="POST", json=update_refund_result)
            channel.basic_publish(exchange=exchangename, routing_key="refund.error", 
                body=update_refund_message, properties=pika.BasicProperties(delivery_mode = 2)) 
            # make message persistent within the matching queues until it is received by some receiver 
            # (the matching queues have to exist and be durable and bound to the exchange)
      
            print("\nRefund status ({:d}) published to the RabbitMQ Exchange:".format(
                code), update_refund_result)

            # Return error
            return {
                "code": 500,
                "message": "Updating refund details failed sent for error handling."
            }
        
        print('\n-----Invoking refund_log microservice-----')
        print('\n-----Publishing the (update refund info) message with routing_key=refund.info-----')        
        invoke_http(refund_log_URL, method="POST", json=update_refund_result)
        channel.basic_publish(exchange=exchangename, routing_key="refund.info", 
            body=update_refund_message)
        print("\nRefund published to RabbitMQ Exchange.")

        print("\n-----Successfully Invoked Refund Microservice-----")

        message = f"""
                <html>
                    <body>
                        <h1>Refund Rejected</h1>
                        <p>We have rejected your refund request of your ticket</p>
                        <ul>
                            <li><strong>User ID:</strong> {user_response["user_id"]}</li>
                            <li><strong>Event ID:</strong> {refund['event_id']}</li>
                            <li><strong>Ticket ID:</strong> {refund['ticket_id']}</li>
                            <li><strong>Refund Status:</strong> Rejected </li>
                        </ul>
                        <p>Best regards,<br>Ticketmaster</p>
                    </body>
                </html>
                """

        print('\n-----Invoking email microservice-----')
        email_refund_result = invoke_http(email_URL, method='POST', json={
            "to_email": user_response["email"],
            "html_content": message
        })
        print("email_refund_result:", email_refund_result)
        email_refund_message = json.dumps(email_refund_result)

        code = email_refund_result["code"]
        
        if code not in range(200, 300):
            # Inform the error microservice
            print('\n-----Invoking error microservice as send email fails-----')
            print('\n-----Publishing the (email error) message with routing_key=email.error-----')

            invoke_http(error_URL, method="POST", json=email_refund_result)
            channel.basic_publish(exchange=exchangename, routing_key="email.error", 
                body=email_refund_message, properties=pika.BasicProperties(delivery_mode = 2)) 
            # make message persistent within the matching queues until it is received by some receiver 
            # (the matching queues have to exist and be durable and bound to the exchange)

            # - reply from the invocation is not used;
            # continue even if this invocation fails        
            print("\nEmail status ({:d}) published to the RabbitMQ Exchange:".format(
                code), email_refund_result)
             
            return {
                "code": 500,
                "message": "Email failure sent for error handling."
            }
        
        print('\n-----Invoking refund_log microservice-----')
        print('\n-----Publishing the (email info) message with routing_key=email.info-----')
        invoke_http(refund_log_URL, method="POST", json=email_refund_result)
        channel.basic_publish(exchange=exchangename, routing_key="email.info", 
            body=email_refund_message)
        print("\Email published to RabbitMQ Exchange.")

        print('\n-----Successfully Invoked Email microservice-----')

        print('\n-----Successfully Invoked Refund Microservice-----')
        return {
            "code": 201,
            "message": "Refund request rejected and closed."
        }
    
    else:
        return {
            "code": 400,
            "message": "Invalid decision. Must be approve or reject."
        }

def get_user_data(user_id):
    user_response = invoke_http(f"{user_URL}/{user_id}", method='GET')
    if user_response.get("code") == 200:
        return user_response.get("data")
    else:
        return None

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