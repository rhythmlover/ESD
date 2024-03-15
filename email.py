from flask import Flask, request, jsonify
import os
import barcode
from barcode.writer import ImageWriter
import emailjs
import requests

app = Flask(__name__)

@app.route("/send_email", methods=['POST'])
def send_email():
    if request.is_json:
        try:
            email_data = request.get_json()
            print("\nReceived an email request:", email_data)

            # Send email
            send_result = send_email_service(email_data)
            if send_result:
                return jsonify({"code": 200, "message": "Email sent successfully.", "data": email_data}), 200
            else:
                return jsonify({"code": 500, "message": "Failed to send email."}), 500

        except Exception as e:
            return jsonify({"code": 500, "message": "Internal server error: " + str(e)}), 500

    return jsonify({"code": 400, "message": "Invalid JSON input."}), 400

def send_email_service(email_data):
    template_params = {
        'name': email_data.get('name', ''),
        'email': email_data.get('email', ''),
        'message': email_data.get('message', ''),
        'barcode_image': email_data.get('barcode_image', '')
    }
    emailjs.send('service_id', 'template_id', template_params, 'user_id')
    return True

def send_telegram_message(message):
    # Replace 'YOUR_BOT_TOKEN' and 'YOUR_CHAT_ID' with your actual bot token and chat ID
    bot_token = 'YOUR_BOT_TOKEN'
    chat_id = 'YOUR_CHAT_ID'
    telegram_api_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    
    payload = {
        'chat_id': chat_id,
        'text': message
    }

    response = requests.post(telegram_api_url, json=payload)

    if response.status_code == 200:
        print("Telegram message sent successfully.")
    else:
        print(f"Failed to send Telegram message. Status code: {response.status_code}")

if __name__ == "__main__":
    print("This is Flask " + os.path.basename(__file__) + " for sending emails...")
    app.run(host="0.0.0.0", port=5003, debug=True)