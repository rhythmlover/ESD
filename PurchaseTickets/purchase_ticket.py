from flask import Flask, request, jsonify
from flask_cors import CORS
import os, sys
from invokes import invoke_http
import pika
import json
import amqp_connection

app = Flask(__name__)
CORS(app)

user_URL = "http://localhost:5004/users"
ticket_URL = "http://localhost:5001/tickets"
payment_URL = "http://localhost:5002/process_payment"
email_URL = "http://localhost:5003/send_email"

# Using RabbitMQ as the message broker
error_URL = "http://localhost:5100/log/error"
activity_log_URL = "http://localhost:5100/log/activity"

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
            user_id = ticket_request.get('user_id')

            # Step 1: Fetch user details
            user_response = get_user_data(user_id)
            message = json.dumps(user_response)
            if not user_response:
                # Inform the error microservice
                print('\n\n-----Invoking error microservice as get user fails-----')
                print('\n\n-----Publishing the (get user error) message with routing_key=user.error-----')

                invoke_http(error_URL, method="POST", json=user_response)
                channel.basic_publish(exchange=exchangename, routing_key="user.error", 
                    body=message, properties=pika.BasicProperties(delivery_mode = 2))
                # make message persistent within the matching queues until it is received by some receiver 
                # (the matching queues have to exist and be durable and bound to the exchange)

                # - reply from the invocation is not used;
                # continue even if this invocation fails        
                print("\Get user status ({:d}) published to the RabbitMQ Exchange:".user_response)

                return jsonify({"code": 404, "message": "User not found."}), 404

            # Step 2: Create Ticket
            print('\n-----Invoking Ticket microservice-----')
            ticket_creation_data = invoke_http(f"{ticket_URL}/create", method='POST', json=ticket_request)
            if ticket_creation_data["code"] not in range(200, 300):
                
                # Inform the error microservice
                print('\n\n-----Invoking error microservice as create ticket fails-----')
                print('\n\n-----Publishing the (create ticket error) message with routing_key=createTicket.error-----')

                invoke_http(error_URL, method="POST", json=ticket_creation_data)
                channel.basic_publish(exchange=exchangename, routing_key="createTicket.error", 
                    body=message, properties=pika.BasicProperties(delivery_mode = 2))
                # make message persistent within the matching queues until it is received by some receiver 
                # (the matching queues have to exist and be durable and bound to the exchange)

                # - reply from the invocation is not used;
                # continue even if this invocation fails
                print("\Get create ticket status ({:d}) published to the RabbitMQ Exchange:".ticket_creation_data)
                
                return jsonify(ticket_creation_data), ticket_creation_data["code"]
            
            # Get ticket details
            ticket_details_data = invoke_http(f"{ticket_URL}/{ticket_request.get('ticket_id')}", method='GET')
            print('\n-----Successfully Invoked Ticket microservice-----')

            # record the activity log
            print('\n\n-----Invoking activity_log microservice-----')
            print('\n\n-----Publishing the (ticket details data info) message with routing_key=ticketDetails.info-----')        

            invoke_http(activity_log_URL, method="POST", json=ticket_creation_data)            
            channel.basic_publish(exchange=exchangename, routing_key="ticketDetails.info", 
                body=message)
            print("\Ticket details published to RabbitMQ Exchange.\n")

            # Step 3: Process Payment
            print('\n-----Invoking Payment microservice-----')
            payment_response = invoke_http(payment_URL, method='POST', json={
                "user_id": user_id,
                "ticket_id": ticket_details_data['data']["ticket_id"],
                "amount": ticket_request.get('amount'),
                "currency": "sgd",
                # Hardcoded payment method and customer id for testing
                "payment_method_id": "pm_1OvsxW2LHSKllIVVJ6xs1nRw",
                "customer_id": "cus_PlPj7w7jUycNMl"
            })
            if payment_response["code"] == 200:
                payment_id = payment_response["data"]["id"]

                ticket_update_data = {
                    "payment_id": payment_id
                }
                update_response = invoke_http(f"{ticket_URL}/{ticket_details_data['data']['ticket_id']}/payment", method='PUT', json=ticket_update_data)
                
                if update_response["code"] not in range(200, 300):

                    # Inform the error microservice
                    print('\n\n-----Invoking error microservice as update payment fails-----')
                    print('\n\n-----Publishing the (update payment error) message with routing_key=updatePayment.error-----')

                    invoke_http(error_URL, method="POST", json=update_response)
                    channel.basic_publish(exchange=exchangename, routing_key="updatePayment.error", 
                        body=message, properties=pika.BasicProperties(delivery_mode = 2))
                    # make message persistent within the matching queues until it is received by some receiver 
                    # (the matching queues have to exist and be durable and bound to the exchange)

                    # - reply from the invocation is not used;
                    # continue even if this invocation fails        
                    print("\Get update payment status ({:d}) published to the RabbitMQ Exchange:".update_response)

                    return jsonify(update_response), update_response["code"]
            else:
                return jsonify(payment_response), payment_response["code"]  
            print('\n-----Successfully Invoked Payment microservice-----')  

            # record the activity log
            print('\n\n-----Invoking activity_log microservice-----')
            print('\n\n-----Publishing the (update response data info) message with routing_key=updateResponse.info-----')        

            invoke_http(activity_log_URL, method="POST", json=update_response)            
            channel.basic_publish(exchange=exchangename, routing_key="updateResponse.info", 
                body=message)
            print("\Update response published to RabbitMQ Exchange.\n")


            print('\n-----Invoking Email microservice-----')
            # Step 5: Send Notification
            html_content = f"""
            <html>
                <body>
                    <h1>Purchase Confirmation</h1>
                    <p>Thank you for your purchase. Here are the details of your transaction:</p>
                    <ul>
                        <li><strong>User ID:</strong> {user_id}</li>
                        <li><strong>Payment ID:</strong> {payment_id}</li>
                        <li><strong>Amount Paid:</strong> ${round(((payment_response["data"].get("amount", "N/A"))/100),2)}</li>
                        <li><strong>Age Verified:</strong> {ticket_details_data["data"].get("age_verified")}</li>
                        <li><strong>Transaction Date:</strong> {ticket_details_data["data"].get("created_at", "N/A")}</li>
                        <li><strong>Event ID:</strong> {ticket_details_data["data"].get("event_id", "N/A")}</li>
                        <li><strong>Ticket ID:</strong> {ticket_details_data["data"].get("ticket_id", "N/A")}</li>
                        <li><strong>Ticket Redeemed:</strong> {ticket_details_data["data"].get("ticket_redeemed")}</li>
                    </ul>
                    <p>Best regards,<br>Ticketmaster</p>
                </body>
            </html>
            """
            # html_content_json = json.dumps({**payment_response["data"], **ticket_details_data["data"]["amount"]})
            email_response = invoke_http(email_URL, method='POST', json={
                "to_email": user_response["email"],
                "html_content": html_content
            })
            if email_response["code"] not in range(200, 300):

                # Inform the error microservice
                print('\n\n-----Invoking error microservice as send email fails-----')
                print('\n\n-----Publishing the (get user error) message with routing_key=sendEmail.error-----')

                invoke_http(error_URL, method="POST", json=email_response)
                channel.basic_publish(exchange=exchangename, routing_key="sendEmail.error", 
                    body=message, properties=pika.BasicProperties(delivery_mode = 2))
                # make message persistent within the matching queues until it is received by some receiver 
                # (the matching queues have to exist and be durable and bound to the exchange)

                # - reply from the invocation is not used;
                # continue even if this invocation fails        
                print("\Get send email ({:d}) published to the RabbitMQ Exchange:".email_response)

                return jsonify(email_response), email_response["code"]
            print('\n-----Successfully Invoked Email microservice-----')

            # record the activity log
            print('\n\n-----Invoking activity_log microservice-----')
            print('\n\n-----Publishing the (email response data info) message with routing_key=email.info-----')        

            invoke_http(activity_log_URL, method="POST", json=email_response)            
            channel.basic_publish(exchange=exchangename, routing_key="email.info", 
                body=message)
            print("\Email response published to RabbitMQ Exchange.\n")
 
            
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
            "code": 201,
            "message": "Ticket purchased successfully."
        }), 201
    else:
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5200, debug=True)