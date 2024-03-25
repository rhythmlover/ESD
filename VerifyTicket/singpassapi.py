# Singpass sandbox api microservice - to call dob from a set of dummy data. 
# parameters to send: UEN/UNIFIN
# Dummy datas
# T15LP0010D/F1612345P
# 53235113D/S6005052Z
# T08LL1728H/S9912360E
# T15LP8766B/S9912361C
# 53235176B/S6005051A
# 53235181M/S6005048A
# 53235297A/S9812386E
# T15LP0010D/F1612345P
# 53235183E/F1612350K
# T14LL0058A/S9812380F
# 198104639K/S9812380F
# S48FC1953T/F1612350K
# T15LL0004H/S9812386E
# T14LP0063A/S6005051A
# T15LP0011L/F1612350K
# T15LP0005A/S9912374E

from flask import Flask, jsonify, request
import requests
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import firestore, credentials

# Initialise firebase 
app = Flask(__name__)
cred = credentials.Certificate("esd-ticketing-firebase-adminsdk-dxgtc-363d36e381.json")
firebase_admin.initialize_app(cred)
db = firestore.client()
@app.route('/verify-age', methods=['GET'])
def verify_age():
    # Extracting parameters from query parameters
    UEN_id = request.args.get('UEN')
    UNIFIN_id = request.args.get('UNIFIN')

    if not UEN_id or not UNIFIN_id:
        return jsonify({'error': 'UEN or UNIFIN missing'}), 400

    # Construct the API URL to fetch DOB data
    api_url = f"https://sandbox.api.myinfo.gov.sg/biz/v2/entity-person-sample/{UEN_id}/{UNIFIN_id}"

    try:
        # Make the request to the external DOB API
        response = requests.get(api_url)
        response.raise_for_status()
        dob_data = response.json()

        dob_str = dob_data.get('person', {}).get('dob', {}).get('value', 'DOB not found')
        if dob_str:
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

            if age >= 21:
                return jsonify({'Person is above 21': True}), 200
            else:
                return jsonify({'Person is above 21': False}), 200
        else:
            return jsonify({'error': 'DOB not found'}), 404
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500

    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
