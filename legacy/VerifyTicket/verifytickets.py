# verify tickets complex microservice
import requests
from flask import Flask, request, jsonify
import os

from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
# Endpoint to start the orchestration
@app.route('/orchestrate', methods=['GET'])
def orchestratewithsingpass(): 
    ticket_id = request.args.get('ticket_id')
    UEN_id = request.args.get('UEN')
    UNIFIN_id = request.args.get('UNIFIN')


    if not ticket_id or not UEN_id or not UNIFIN_id:
        return jsonify({'error': 'Missing required parameters'}), 400

    # Step 1: Check ticket status
    ticket_status_response = requests.get(f"http://localhost:5001/get-ticket-status?ticket_id={ticket_id}")
    if ticket_status_response.status_code != 200 or ticket_status_response.json().get('ticket_redeemed') == True:
        return jsonify({'error': 'Ticket already redeemed or could not check ticket status'}), ticket_status_response.status_code

    # Step 2: Verify user's age using SingPass API
    age_verification_response = requests.get(f"http://localhost:5003/verify-age?UEN={UEN_id}&UNIFIN={UNIFIN_id}")
    if age_verification_response.status_code != 200 or not age_verification_response.json().get('Person is above 21'):
        return jsonify({'error': 'Age verification failed or user is underage'}), age_verification_response.status_code

    # Step 3: Update verified status in the database
    update_response = requests.post(f"http://localhost:5002/update-verified?ticket_id={ticket_id}&UEN={UEN_id}")
    if update_response.status_code == 200:
        return jsonify({'message': 'Ticket verification and update completed successfully'}), 200
    else:
        return jsonify({'error': 'Failed to update verified status'}), update_response.status_code


@app.route('/orchestrate2', methods=['GET'])
def orchestratewithoutsingpass():
    ticket_id = request.args.get('ticket_id')
    if not ticket_id:
        return jsonify({'error': 'Missing ticket_id'}), 400
    

    # Step 1: Verify if the ticket has been redeemed by calling the first microservice
    verify_url = f"http://localhost:5001/get-ticket-status?ticket_id={ticket_id}"
    verify_response = requests.get(verify_url)
    if verify_response.status_code != 200:
        return jsonify({'error': 'Error checking ticket status'}), verify_response.status_code
    
    ticket_info = verify_response.json()
    if 'ticket_redeemed' in ticket_info and ticket_info['ticket_redeemed']:
        return jsonify({'message': 'Ticket already redeemed or not found.'}), 400
    elif not ticket_info.get('ticket_redeemed', False):
        # Ticket not redeemed, proceed to append to user's current tickets
        update_url = f"http://localhost:5002/update-verified?ticket_id={ticket_id}"

        update_response = requests.post(update_url)  # Adjust based on the actual endpoint and method
        if update_response.status_code == 200:
            return jsonify({'message': 'Ticket appended to user successfully.'}), 200
        else:
            return jsonify({'error': 'Error appending ticket to user'}), update_response.status_code

    return jsonify({'error': 'Unexpected error'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)