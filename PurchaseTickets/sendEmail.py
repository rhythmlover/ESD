# from flask import Flask, request, jsonify
# import os
# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail
# import requests

# app = Flask(__name__)

# @app.route("/send_email", methods=['POST'])
# def send_email():
#     if request.is_json:
#         try:
#             email_data = request.get_json()
#             print("\nReceived an email request:", email_data)

#             from_email = 'ethantankw@gmail.com'
#             to_emails = email_data.get('email', '')
#             subject = email_data.get('subject', 'No Subject')
#             content = f"<strong>{email_data.get('message', 'No message provided')}</strong>"
#             # Send email
#             send_result = send_email_service(from_email, to_emails, subject, content)
#             if send_result:
#                 return jsonify({"code": 200, "message": "Email sent successfully.", "data": email_data}), 200
#             else:
#                 return jsonify({"code": 500, "message": "Failed to send email."}), 500

#         except Exception as e:
#             return jsonify({"code": 500, "message": "Internal server error: " + str(e)}), 500

#     return jsonify({"code": 400, "message": "Invalid JSON input."}), 400

# def send_email_service(from_email, to_emails, subject, content):
#     message = Mail(
#         from_email=from_email,
#         to_emails=to_emails,
#         subject=subject,
#         html_content=content
#     )
#     try:
#         sg = SendGridAPIClient("")
#         response = sg.send(message)
#         print(response.status_code)
#         print(response.body)
#         print(response.headers)
#         return True
#     except Exception as e:
#         print(f"Error sending email: {e}")
#         if hasattr(e, 'response') and e.response:
#             print(e.response.content)
#         return False

# if __name__ == "__main__":
#     print("This is Flask " + os.path.basename(__file__) + " for sending emails...")
#     app.run(host="0.0.0.0", port=5003, debug=True)