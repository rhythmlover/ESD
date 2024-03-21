# Singpass sandbox api microservice - to call dob from a set of dummy data. 
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

app = Flask(__name__)

@app.route('/get-dob', methods=['GET'])
def get_dob():
    # Construct the API URL
    UEN_id = request.args.get('UEN')
    UNIFIN_id = request.args.get('UNIFIN')
    if not UEN_id or not UNIFIN_id:
        return jsonify({"error": "Missing UEN or UNIFIN"}), 400

    api_url = f"https://sandbox.api.myinfo.gov.sg/biz/v2/entity-person-sample/{UEN_id}/{UNIFIN_id}"

    try:
        # Make the GET request to the external API
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for HTTP error codes

        # Extract the JSON content
        data = response.json()

        # Retrieve the 'dob' attribute
        dob_str = data.get('person',{}).get('dob',{}).get('value','DOB not found')
        if dob_str:
            # convert dob_str to datetime object
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
            # Calculate the age
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

            # Check if the person is 21 years of age or above
            is_21_or_above = age >= 21
            return jsonify({"is_21_or_above": is_21_or_above}), 200
        else:
            return jsonify({"error": "DOB not found in response"}), 404
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
