from flask import Flask, request, jsonify
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)

@app.route('/send-email', methods=['POST'])
def send_email():
    """
    Sends an email using the provided data.
    ---
    parameters:
        
    responses:
        200:
            description: Sends email to the recipient
        400:
            description: Error occurred in sending email
    Returns:
        A JSON response containing the status code and a message indicating the result of the email sending process.
    """
    data = request.get_json()

    sender_email = "dominictehcoding@gmail.com"
    sender_password = "xeckub-6pacpY-mopbew"
    receiver_email = data['email']
    subject = data['subject']
    message = data['message']

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()

        return jsonify(
            {
                "code": 200,
                "message": "Email sent successfully."
            }
        ), 200
    except Exception as e:
        return jsonify(
            {
                'code': 400,
                'message': "An error occurred while sending the email." + str(e)
            }
        ), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5003, debug=True)