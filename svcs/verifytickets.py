# verify tickets complex microservice
import requests
from flask import Flask, request, jsonify
import os, sys
import logging
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
@app.route('/verify_ticket', methods=['POST'])
def verify_ticket():
    if not request.json:
        return jsonify({'error': 'Missing request body'}), 400

    try:
        body_request = request.json
        ticket_id = body_request.get('ticket_id')
        UEN_id = body_request.get('UEN')
        UNIFIN_id = body_request.get('UNIFIN')
        qr_code = body_request.get('qr_code')

        if UEN_id and UNIFIN_id:
            result = orchestratewithsingpass(ticket_id, UEN_id, UNIFIN_id, qr_code)
            print('\n------------------------')
            print('\nresult: ', result)
            return result
        else:
            result = orchestratewithoutsingpass(ticket_id, qr_code)
            print('\n------------------------')
            print('\nresult: ', result)
            return result
    except Exception as e:
        # Unexpected error in code
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        ex_str = str(e) + " at " + str(exc_type) + ": " + \
            fname + ": line " + str(exc_tb.tb_lineno)
        print(ex_str)

        return jsonify({
            "code": 500,
            "message": "verifyticket.py internal error: " + ex_str
        }), 500


def orchestratewithsingpass(ticket_id, UEN_id, UNIFIN_id, qr_code):
    if not ticket_id or not UEN_id or not UNIFIN_id or not qr_code:
        return jsonify({'error': 'Missing required parameters'}), 400

    # Step 1: Check ticket status and QR code match
    ticket_status_response = requests.get(
        f"http://localhost:5009/get-ticket-status/{ticket_id}/{qr_code}")
    
    if ticket_status_response.status_code != 200 or ticket_status_response.json().get('ticket_redeemed') == True:
        return jsonify({'error': 'Ticket already redeemed or could not check ticket status'}), ticket_status_response.status_code

    # Step 2: Verify user's age using SingPass API
    age_verification_response = requests.get(
        f"http://localhost:5010/verify-age?UEN={UEN_id}&UNIFIN={UNIFIN_id}")
    
    if age_verification_response.status_code != 200 or not age_verification_response.json().get('Person is above 21'):
        return jsonify({'error': 'Age verification failed or user is underage'}), age_verification_response.status_code

    # Step 3: Update verified status in the database
    update_data = {
        'ticket_id': ticket_id,
        'UEN_id' : UEN_id
    }
    update_response = requests.post("http://localhost:5001/update-verified", json=update_data)
    
    if update_response.status_code == 200:
        return jsonify({'message': 'Ticket verification and update completed successfully'}), 200
    else:
        error_message = f"Failed to update verified status. Status code: {update_response.status_code}, Response: {update_response.json()}"
        return jsonify({'error': error_message}), update_response.status_code

def orchestratewithoutsingpass(ticket_id, qr_code):
    if not ticket_id:
        return jsonify({'error': 'Missing ticket_id'}), 400

    try:
        # Step 1: Check ticket status and QR code match
        verify_response = requests.get(
            f"http://localhost:5009/get-ticket-status/{ticket_id}/{qr_code}")
        
        print(f"Verify Response Status Code: {verify_response.status_code}")
        print(f"Verify Response Text: {verify_response.text}")
        
        if verify_response.status_code != 200 or verify_response.json().get('ticket_redeemed') == True:
            return jsonify({'error': 'Ticket already redeemed or could not check ticket status'}), verify_response.status_code

        ticket_info = verify_response.json()
        if 'ticket_redeemed' in ticket_info and ticket_info['ticket_redeemed']:
            return jsonify({'message': 'Ticket already redeemed or not found.'}), 400
        elif not ticket_info.get('ticket_redeemed', False):
            # Ticket not redeemed, proceed to append to user's current tickets
            # Step 2: Update verified status in the database
            update_data = {
                'ticket_id': ticket_id,
                'UEN_id': None  # We're not using UEN_id in this case
            }
            
            update_response = requests.post("http://localhost:5001/update-verified", json=update_data)
            
            print(f"Update Response Status Code: {update_response.status_code}")
            print(f"Update Response Text: {update_response.text}")
            
            if update_response.status_code == 200:
                return jsonify({'message': 'Ticket appended to user successfully.'}), 200
            else:
                error_message = f"Failed to update verified status. Status code: {update_response.status_code}, Response: {update_response.json()}"
                print(error_message)  # Print the error message for debugging
                return jsonify({'error': error_message}), update_response.status_code
    except Exception as e:
        print(f"Error in orchestratewithoutsingpass: {str(e)}")  # Print the specific error message for debugging
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5300, debug=True)
