from flask import Flask, request, jsonify
from flask_cors import CORS
import os, sys
from invokes import invoke_http
import pika
import json
import amqp_connection
import qrcode
import io
import os
import base64

app = Flask(__name__)
CORS(app)

user_URL = "http://localhost:5001/users"
ticket_URL = "http://localhost:5002/tickets"
payment_URL = "http://localhost:5007/process_payment"
email_URL = "http://localhost:5008/send_email"

exchangename = "ticketing_topic"
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
            body_request = request.get_json()
            print("\nReceived a refund in JSON:", body_request)

            # Step 1: Fetch user details
            user_id = body_request.get('user_id')
            user_response = get_user_data(user_id)
            if not user_response:
                return jsonify({"code": 404, "message": "User not found."}), 404

            # Create Ticket
            print('\n-----Invoking Ticket microservice-----')
            ticket_creation_data = invoke_http(f"{ticket_URL}/create", method='POST', json=body_request)
            print('creating_ticket_data:', ticket_creation_data)
            ticket_message = json.dumps(ticket_creation_data)        

            if ticket_creation_data["code"] not in range(200, 300):
                print('\n-----Invoking error microservice as create ticket fails-----')
                print('\n-----Publishing the (create ticket error) message with routing_key=create_ticket.error-----')

                channel.basic_publish(exchange=exchangename, routing_key="create_ticket.error", 
                    body=ticket_message, properties=pika.BasicProperties(delivery_mode = 2))
                # make message persistent within the matching queues until it is received by some receiver 
                # (the matching queues have to exist and be durable and bound to the exchange)

                print("\nCreate ticket status ({:d}) published to the RabbitMQ Exchange:".format(ticket_creation_data["code"]), ticket_creation_data)

                print("\n-----Invoking Ticket Microservice failed-----")
                # Return error
                return {
                    "code": 500,
                    "message": "Failed to create ticket."
                }
            
            print('\n-----Invoking activity_log microservice-----')
            print('\n-----Publishing the (ticket creation data info) message with routing_key=create_ticket.info-----')

            channel.basic_publish(exchange=exchangename, routing_key="create_ticket.info",
                body=ticket_message)

            print("\nTicket creation published to RabbitMQ Exchange.")

            print('\n-----Successfully Invoked Ticket microservice-----')

            # Get ticket details for payment process
            print('\n-----Invoking Ticket microservice-----')
            print('\n-----Getting ticket details for payment-----')
            ticket_details_data = invoke_http(f"{ticket_URL}/{body_request.get('ticket_id')}", method='GET')
            print('ticket_details_data:', ticket_details_data)
            ticket_details_message = json.dumps(ticket_details_data)

            if ticket_details_data["code"] not in range(200, 300):
                print('\n-----Invoking error microservice as get ticket details fails-----')
                print('\n-----Publishing the (get ticket details error) message with routing_key=get_ticket_details.error-----')

                channel.basic_publish(exchange=exchangename, routing_key="get_ticket_details.error", 
                    body=ticket_details_message, properties=pika.BasicProperties(delivery_mode = 2))
                # make message persistent within the matching queues until it is received by some receiver 
                # (the matching queues have to exist and be durable and bound to the exchange)

                print("\nGet ticket details status ({:d}) published to the RabbitMQ Exchange:".format(ticket_details_data["code"]), ticket_details_data)

                print("\n-----Invoking Ticket Microservice failed-----")
                # Return error
                return {
                    "code": 500,
                    "message": "Failed to get ticket details."
                }
            
            print('\n-----Invoking activity_log microservice-----')
            print('\n-----Publishing the (ticket details data info) message with routing_key=get_ticket_details.info-----')
            
            channel.basic_publish(exchange=exchangename, routing_key="get_ticket_details.info",
                body=ticket_details_message)

            print("\nTicket details published to RabbitMQ Exchange.")

            print('\n-----Successfully Invoked Ticket microservice-----')
            print('\n-----Successfully Get Ticket Details for payment-----')

            # Process Payment
            print('\n-----Invoking Payment microservice-----')            
            payment_response = invoke_http(payment_URL, method='POST', json={
                "user_id": user_id,
                "ticket_id": ticket_details_data['data']["ticket_id"],
                "amount": body_request.get('amount'),
                "currency": "sgd",
                # Hardcoded payment method and customer id for testing
                "payment_method_id": "pm_1OweLXKfHG7YK88cDu9xlKSL",
                "customer_id": "cus_PmCkFZartm4jWy"
            })
            print('payment_response:', payment_response)
            payment_message = json.dumps(payment_response)

            if payment_response["code"] not in range(200, 300):
                print('\n-----Invoking error microservice as process payment fails-----')
                print('\n-----Publishing the (process payment error) message with routing_key=process_payment.error-----')

                channel.basic_publish(exchange=exchangename, routing_key="process_payment.error", 
                    body=payment_message, properties=pika.BasicProperties(delivery_mode = 2))
                # make message persistent within the matching queues until it is received by some receiver 
                # (the matching queues have to exist and be durable and bound to the exchange)

                print("\nProcess payment status ({:d}) published to the RabbitMQ Exchange:".format(payment_response["code"]), payment_response)

                print("\n-----Invoking Payment Microservice failed-----")
                # Return error
                return {
                    "code": 500,
                    "message": "Failed to process payment."
                }
            
            print('\n-----Invoking activity_log microservice-----')
            print('\n-----Publishing the (payment response data info) message with routing_key=process_payment.info-----')

            channel.basic_publish(exchange=exchangename, routing_key="process_payment.info",
                body=payment_message)
            
            print("\nPayment response published to RabbitMQ Exchange.")
            
            print('\n-----Successfully Invoked Payment microservice-----')

            # Update Ticket
            print('\n-----Invoking Ticket microservice-----')
            payment_id = payment_response["data"]["id"]
            update_response = invoke_http(f"{ticket_URL}/{ticket_details_data['data']['ticket_id']}/payment", method='PUT', json={
                "payment_id": payment_id,
                "charge_id": payment_response["data"]["charge_id"]
            })
            print('update_response:', update_response)
            update_message = json.dumps(update_response)

            if update_response["code"] not in range(200, 300):
                print('\n-----Invoking error microservice as update ticket fails-----')
                print('\n-----Publishing the (update ticket error) message with routing_key=update_ticket.error-----')

                channel.basic_publish(exchange=exchangename, routing_key="update_ticket.error", 
                    body=update_message, properties=pika.BasicProperties(delivery_mode = 2))
                # make message persistent within the matching queues until it is received by some receiver 
                # (the matching queues have to exist and be durable and bound to the exchange)

                print("\nUpdate ticket status ({:d}) published to the RabbitMQ Exchange:".format(update_response["code"]), update_response)

                print("\n-----Invoking Ticket Microservice failed-----")
                # Return error
                return {
                    "code": 500,
                    "message": "Failed to update ticket."
                }
            
            print('\n-----Invoking activity_log microservice-----')
            print('\n-----Publishing the (update ticket response data info) message with routing_key=update_ticket.info-----')

            channel.basic_publish(exchange=exchangename, routing_key="update_ticket.info",
                body=update_message)
            
            print("\nUpdate ticket published to RabbitMQ Exchange.")

            print('\n-----Successfully Invoked Ticket microservice-----')

            print('\n-----Invoking Email microservice-----')
            # Send Notification
            qr_code_data = ticket_details_data['data']['qr_code']
            qr_code_image = generate_qr_code_image(qr_code_data)

            if qr_code_image:
                image_base64 = convert_image_to_base64(qr_code_image)

                # Attach the base64-encoded image as a file to the email
                attachment_data = {
                    "filename": "qr_code.png",
                    "data": image_base64
                }

            html_content = f"""
            <html>
                <body>
                    <h1>Purchase Confirmation</h1>
                    <p>Thank you for your purchase. Here are the details of your transaction:</p>
                    <p>Attached is the QR code for your ticket</p>
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
            email_response = invoke_http(email_URL, method='POST', json={
                "to_email": user_response["email"],
                "html_content": html_content,
                "attachment_data": attachment_data
            })
            print('email_response:', email_response)
            email_message = json.dumps(email_response)

            if email_response["code"] not in range(200, 300):
                print('\n-----Invoking error microservice as send email fails-----')
                print('\n-----Publishing the (get email error) message with routing_key=email.error-----')

                channel.basic_publish(exchange=exchangename, routing_key="email.error", 
                    body=email_message, properties=pika.BasicProperties(delivery_mode = 2))
                # make message persistent within the matching queues until it is received by some receiver 
                # (the matching queues have to exist and be durable and bound to the exchange)

                # - reply from the invocation is not used;
                # continue even if this invocation fails        
                print("\nSend email ({:d}) published to the RabbitMQ Exchange:".format(email_response["code"]), email_response)

                print("\n-----Invoking Email Microservice failed-----")

                # Return error
                return {
                    "code": 500,
                    "message": "Failed to send email."
                }
            
            print('\n-----Invoking activity_log microservice-----')
            print('\n-----Publishing the (email response data info) message with routing_key=email.info-----')

            channel.basic_publish(exchange=exchangename, routing_key="email.info", 
                body=email_message)
            
            print("\nEmail response published to RabbitMQ Exchange.")

            print('\n-----Successfully Invoked Email microservice-----')
            
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            ex_str = str(e) + " at " + str(exc_type) + ": " + fname + ": line " + str(exc_tb.tb_lineno)
            print(ex_str)

            return jsonify({
                "code": 500,
                "message": "purchase_ticket.py internal error: " + ex_str
            }), 500

        print('\n-----Successfully Purchased Ticket-----')
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
    
def generate_qr_code_image(qr_code_data):
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_code_data)
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")
        return qr_image
    except Exception as e:
        print(f"Error generating QR code: {e}")
        return None

def convert_image_to_base64(image):
    try:
        buffered = io.BytesIO()
        image.save(buffered)
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return base64_image
    except Exception as e:
        print(f"Error converting image to base64: {e}")
        return None

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5200, debug=True)