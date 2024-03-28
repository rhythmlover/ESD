# verify tickets complex microservice
import requests
from flask import Flask, request, jsonify
import os, sys

from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/verify_ticket', methods=['POST'])
def verify_ticket():
    if not request.json:
        return jsonify({'error': 'Missing request body'}), 400

    try:
        body_request = request.json
        ticket_id = body_request.get('ticket_id')
        UEN_id = body_request.get('UEN_id')
        UNIFIN_id = body_request.get('UNIFIN_id')
        qr_code = body_request.get('qr_code')

        if UEN_id and UNIFIN_id:
            result = orchestratewithsingpass(ticket_id, UEN_id, UNIFIN_id, qr_code)
            print('\n------------------------')
            print('\nresult: ', result)
            return jsonify(result), result["code"]
        else:
            result = orchestratewithoutsingpass(ticket_id, qr_code)
            print('\n------------------------')
            print('\nresult: ', result)
            return jsonify(result), result["code"]
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
    if not ticket_id or not UEN_id or not UNIFIN_id:
        return jsonify({'error': 'Missing required parameters'}), 400

    # Step 1: Check ticket status
    ticket_status_response = requests.get(
        f"http://host.docker.internal:5011/get-ticket-status?ticket_id={ticket_id}")
    if ticket_status_response.status_code != 200 or ticket_status_response.json().get('ticket_redeemed') == True:
        return jsonify({'error': 'Ticket already redeemed or could not check ticket status'}), ticket_status_response.status_code
    
    # Step 2: Check QR code match
    qr_code_response = requests.get(f"http://host.docker.internal:5002/update_ticket_redeem?ticket_id={ticket_id}?qr_code={qr_code}")
    if qr_code_response.status_code != 200:
        return jsonify({'error': 'QR code does not match'}), qr_code_response.status_code

    # Step 3: Verify user's age using SingPass API
    age_verification_response = requests.get(
        f"http://host.docker.internal:5010/verify-age?UEN={UEN_id}&UNIFIN={UNIFIN_id}")
    if age_verification_response.status_code != 200 or not age_verification_response.json().get('Person is above 21'):
        return jsonify({'error': 'Age verification failed or user is underage'}), age_verification_response.status_code

    # Step 4: Update verified status in the database
    update_response = requests.post(
        f"http://host.docker.internal:5001/update-verified?ticket_id={ticket_id}&UEN={UEN_id}")
    if update_response.status_code == 200:
        return jsonify({'message': 'Ticket verification and update completed successfully'}), 200
    else:
        return jsonify({'error': 'Failed to update verified status'}), update_response.status_code


def orchestratewithoutsingpass(ticket_id, qr_code):
    if not ticket_id:
        return jsonify({'error': 'Missing ticket_id'}), 400

    # Step 1: Verify if the ticket has been redeemed by calling the first microservice
    verify_url = f"http://host.docker.internal:5011/get-ticket-status?ticket_id={ticket_id}"
    verify_response = requests.get(verify_url)
    if verify_response.status_code != 200:
        return jsonify({'error': 'Error checking ticket status'}), verify_response.status_code

    ticket_info = verify_response.json()
    if 'ticket_redeemed' in ticket_info and ticket_info['ticket_redeemed']:
        return jsonify({'message': 'Ticket already redeemed or not found.'}), 400
    elif not ticket_info.get('ticket_redeemed', False):
        # Ticket not redeemed, proceed to append to user's current tickets
        update_url = f"http://host.docker.internal:5001/update-verified?ticket_id={ticket_id}"

        # Adjust based on the actual endpoint and method
        update_response = requests.post(update_url)
        if update_response.status_code == 200:
            return jsonify({'message': 'Ticket appended to user successfully.'}), 200
        else:
            return jsonify({'error': 'Error appending ticket to user'}), update_response.status_code
        
    # Step 2: Check QR code match
    qr_code_response = requests.get(f"http://host.docker.internal:5002/update_ticket_redeem?ticket_id={ticket_id}?qr_code={qr_code}")
    if qr_code_response.status_code != 200:
        return jsonify({'error': 'QR code does not match'}), qr_code_response.status_code

    return jsonify({'error': 'Unexpected error'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5300, debug=True)
