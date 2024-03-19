# verify tickets complex microservice
import requests
from flask import Flask, request, jsonify
import os

# if user clicks on verify with singpass
# ===
# calling verification microservice HTTP GET


# <to update> User's ticket ID 

app = Flask(__name__)

# verification microservice url
VERIFICATION_MICROSERVICE_URL = "http://127.0.0.1:5001/get-ticket-status"

@app.route('/verify-ticket', methods=['GET'])
def verify_ticket():
    ticket_id = request.args.get('ticket_id')

    if not ticket_id:
        return jsonify({'error': 'Missing ticket_id'}), 400

    # Call the simple microservice to get the ticket status
    try:
        response = requests.get(VERIFICATION_MICROSERVICE_URL, params={'ticket_id': ticket_id})

        if response.status_code == 200:
            data = response.json()
            # You might want to further process the data here before sending it back
            post_response = requests.post('http://127.0.0.1:5000/update-age-verified',json={'ticket_id':ticket_id})
            update_request = post_response.json()
            return jsonify({
                "code": 200,
                "data": data.get('data'),  # This forwards the response from the simple service
                "message": "Successfully retrieved ticket status."
            })
        else:
            # Forward any errors from the simple microservice
            return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        # Handle connection errors
        return jsonify({
            "code": 500,
            "error": "Failed to connect to the ticket verification service.",
            "exception": str(e)
        }), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True) 

# ===

# === 
# calling singpassapi microservice HTTP GET
# ===
    
# ===
# calling addverifiedusers microservice to update firebase database attribute: "age_verified" based on ticket_id

@app.route('/update-age-verified', methods=['POST'])
def update_age_verified():
    # URL of the addverifiedusers microservice endpoint
    update_url = "http://127.0.0.1:5002/update-verified"
    
    # Prepare the data payload with ticket_id
    ticket_id = request.args.get('ticket_id')
    if not ticket_id:
        return jsonify({'error': 'Missing ticket_id'}), 400
    
    # Make the POST request to the microservice
    try:
        update_response = requests.post(update_url, params={'ticket_id':ticket_id})
        
        # Check if the request was successful
        if update_response.status_code == 200:
            # Assuming the microservice returns a JSON response indicating success
            update_data = update_response.json()
            print(f"Update successful for ticket_id: {ticket_id}. Response: ", update_data)
            return jsonify({"code": 200, "success": True, "data": update_data}), 200
        else:
            print(f"Failed to update age_verified for ticket_id: {ticket_id}. Status Code: {update_response.status_code}")
            return jsonify({"code": update_response.status_code, "error": "Failed to update age_verified."}), update_response.status_code
    except Exception as e:
        print(f"An error occurred while updating age_verified for ticket_id: {ticket_id}. Error: {str(e)}")
        return jsonify({"code": 500, "error": f"An exception occurred: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


# <to insert> If age is verified from singpass



# singpassapi
# update_age_verified(ticket_id)


# <to insert> If age is verified by admin
# verify_ticket(ticket_id)
# update_age_verified(ticket_id)

