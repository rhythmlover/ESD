from flask import Flask, request, jsonify
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)

# Endpoints
@app.route('/send_email', methods=['POST'])
def send_email():
    """
    Sends an email using the provided data.
    ---
    requestBody:
        description: Review details
        required: true
        content:
            application/json:
                schema:
                    properties:
                        to_email: 
                            type: string
                            description: Email of the customer
                        html_content: 
                            type: string
                            description: Refund Details
    responses:
        201:
            description: Email Sent successfully
        400:
            description: Missing required fields in body
        500:
            description: Internal server error
    """

    try:
        required_fields = ['to_email', 'html_content']
        if not all(field in request.json for field in required_fields):
            return jsonify(
                {
                    'code': 400,
                    'message': "Missing required fields. Please provide to_email and html_content."
                }
            ), 400
        
        message = Mail(
        from_email='nigel.koh.2022@smu.edu.sg',
        to_emails=request.json['to_email'],
        subject='Refund Details of Ticket Purchase',
        html_content=request.json['html_content'])

        sg = SendGridAPIClient(
            '')
        response = sg.send(message)
 
        # https://docs.sendgrid.com/api-reference/mail-send/mail-send#responses
        # According to the documentation in sendgrid, the response will be 202 if the email was successfully sent.
        if response.status_code == 202:
            return jsonify(
                {
                    "code": 201,
                    "message": "Email sent successfully to " + request.json['to_email']
                }
            ), 201
    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred while sending the email. " + str(e)
            }
        ), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5008, debug=True)
