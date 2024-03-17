# verifies age by calling singpass api Simple Microservice

from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# Placeholder for SingPass API details
SINGPASS_LOGIN_URL = 'https://example.singpass.gov.sg/login'
CLIENT_ID = 'your_client_id_here'
CLIENT_SECRET = 'your_client_secret_here'
REDIRECT_URI = 'http://localhost:5000/callback'
# Assuming the API provides a way to get user details such as age
SINGPASS_USERINFO_ENDPOINT = 'https://example.singpass.gov.sg/userinfo'

@app.route('/login-with-singpass')
def login_with_singpass():
    # Redirect user to SingPass login page, this URL will be specific to the SingPass API documentation
    # The actual implementation can vary depending on the authentication flow provided by SingPass
    redirect_url = f"{SINGPASS_LOGIN_URL}?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}"
    return redirect(redirect_url)

@app.route('/callback')
def singpass_callback():
    # This route is called by SingPass after the user authenticates
    # Retrieve authorization code from the query parameter
    code = request.args.get('code')

    # Exchange code for a token (assuming OAuth2 flow)
    # The exact details depend on SingPass's implementation
    token_response = requests.post('https://example.singpass.gov.sg/token', data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    })
    token_json = token_response.json()
    access_token = token_json['access_token']

    # Use the token to get user details, including age
    user_response = requests.get(SINGPASS_USERINFO_ENDPOINT, headers={
        'Authorization': f'Bearer {access_token}'
    })
    user_json = user_response.json()
    
    # Placeholder for extracting the age from user_json
    # The structure of user_json depends on the SingPass API
    # Assuming it directly provides age (or calculate based on birthdate)
    user_age = user_json['age']

    # Validate age
    if user_age >= 21:
        return jsonify({'age_validity': True})
    else:
        return jsonify({'age_validity': False})

if __name__ == '__main__':
    app.run(debug=True)




# Configuration (replace with actual values)
BASE_URL = "https://developer.bio-api.singpass.gov.sg/api"
USER_ID = "G2957839M" # use G2834561K to return false
SERVICE_ID = "SingPass"

@app.route('/validate_nric', methods=['POST'])
def validate_nric():
    user_id = request.json.get('user_id', USER_ID)
    service_id = request.json.get('service_id', SERVICE_ID)
    transaction_type = request.json.get('transaction_type', '')

    token_url = f"{BASE_URL}/face/verify/token"
    payload = {
        "user_id": user_id,
        "service_id": service_id,
        "transaction_type": transaction_type
    }

    try:
        response = requests.post(token_url, json=payload)
        response.raise_for_status()
        token_response = response.json()

        if token_response.get('type') == 'error':
            return jsonify({"error": token_response.get('message', {}).get('error_description', '')}), 400
        else:
            token = token_response.get('token', '')
            # Additional logic as needed
            return jsonify({"message": "NRIC validated!", "token": token})
    except requests.RequestException as e:
        return jsonify({"error": "Service is offline or an error occurred", "details": str(e)}), 500

@app.route('/validate_result', methods=['POST'])
def validate_result():
    user_id = request.json.get('user_id', USER_ID)
    service_id = request.json.get('service_id', SERVICE_ID)
    token = request.json.get('token', '')

    validate_url = f"{BASE_URL}/face/verify/validate"
    payload = {
        "user_id": user_id,
        "service_id": service_id,
        "token": token
    }

    try:
        response = requests.post(validate_url, json=payload)
        response.raise_for_status()
        validate_response = response.json()

        # Implement logic based on the response
        # For example, check if validation passed and handle accordingly
        return jsonify(validate_response)
    except requests.RequestException as e:
        return jsonify({"error": "Service is offline or an error occurred", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)