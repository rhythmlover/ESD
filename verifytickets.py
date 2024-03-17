# verify tickets complex microservice
import requests
from flask import Flask, request, jsonify
import os

# if user clicks on verify with singpass
# ===
# calling verification microservice HTTP GET


# <to update> User's ticket ID 
ticket_id = "some_ticket_id"

def verify_ticket(ticket_id):
    verification_url = "http://127.0.0.1:5000/get-ticket-status"

    try:
        # Making the GET request
        response = requests.get(verification_url, params={'ticket_id': ticket_id})

        # Checking if the request was successful
        if response.status_code == 200:
            data = response.json()
            print("Status:", data.get('status'))
            return data.get('status')  # Return the status
        else:
            print("Error: Ticket not found or error occurred.")
            return "Error: Ticket not found or error occurred."
    except Exception as e:
        # Handle any errors that occur during the request
        print(f"Error: An error occurred: {e}")
        return f"Error: An exception occurred: {e}"
# ===

# === 
# calling singpassapi microservice HTTP GET
# ===
    
# ===
# calling addverifiedusers microservice to update firebase database attribute: "age_verified" based on ticket_id
def update_age_verified(ticket_id):
    # URL of the addverifiedusers microservice endpoint
    update_url = "http://127.0.0.1:5000/update-verified"
    
    # Prepare the data payload with ticket_id
    data_payload = {'ticket_id': ticket_id}
    
    # Make the POST request to the microservice
    try:
        update_response = requests.post(update_url, json=data_payload)
        
        # Check if the request was successful
        if update_response.status_code == 200:
            # Assuming the microservice returns a JSON response indicating success
            update_data = update_response.json()
            print(f"Update successful for ticket_id: {ticket_id}.", update_data)
        else:
            print(f"Failed to update age_verified for ticket_id: {ticket_id}. Status Code: {update_response.status_code}")
    except Exception as e:
        print(f"An error occurred while updating age_verified for ticket_id: {ticket_id}. Error: {str(e)}")

# <to insert> If age is verified from singpass
# verify_ticket(ticket_id)
# singpassapi
# update_age_verified(ticket_id)


# <to insert> If age is verified by admin
# verify_ticket(ticket_id)
# update_age_verified(ticket_id)

