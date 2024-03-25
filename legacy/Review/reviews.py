from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import firestore, credentials
from datetime import datetime

# Intialization of Flask app and Firebase Firestore
app = Flask(__name__)
CORS(app)
cred = credentials.Certificate("esd-ticketing-firebase-adminsdk-dxgtc-363d36e381.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Global variables
now = datetime.now()
formatted_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")

# Endpoints
@app.route("/reviews/<string:event_id>", methods=['GET'])
def get_event_reviews(event_id):
    """
    Retrieves all reviews for a specific event.
    ---
    parameters:
        -   in: path
            name: event_id
            required: true
    responses:
        200:
            description: Return the reviews for the event with the specified event_id
        404:
            description: No reviews for this event found.
    """
    reviews_ref = db.collection("reviews").document(
        event_id).collection("event_reviews")
    docs = reviews_ref.stream()

    reviews = []
    for doc in docs:
        reviews.append(doc.to_dict())

    if reviews:
        return jsonify(
            {
                "code": 200,
                "data": reviews
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "No reviews for this event found."
        }
    ), 404

@app.route("/reviews/<string:event_id>", methods=['POST'])
def create_review(event_id):
    """
    Create a review for a specific event.
    ---
    parameters:
        -   in: path
            name: event_id
            required: true
    requestBody:
        description: Review details
        required: true
        content:
            application/json:
                schema:
                    properties:
                        user_id: 
                            type: string
                            description: ID of user who created the review
                        rating: 
                            type: number
                            description: Rating of the event
                        comment: 
                            type: string
                            description: Comment about the event

    responses:
        201:
            description: Feedback created successfully
        400:
            description: Missing required fields in body
        500:
            description: Internal server error

    """
    try:
        required_fields = ['user_id', 'rating', 'comment']
        if not all(field in request.json for field in required_fields):
            return jsonify(
                {
                    "code": 400,
                    "message": "Missing required fields. Please provide user_id, rating, and comment."
                }
            ), 400

        doc_ref = db.collection("reviews").document(
            event_id).collection("event_reviews").document()
        review_id = doc_ref.id
        doc_ref.set({
            'review_id': review_id,
            'rating': request.json['rating'],
            'created_at': formatted_time,
            'user_id': request.json['user_id'],
            'event_id': event_id,
            'comment': request.json['comment'],
            'admin_comment': ''
        })

        return jsonify(
            {
                "code": 201,
                "message": "Review created successfully."
            }
        ), 201
    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred while creating the review. " + str(e)
            }
        ), 500
    
@app.route("/reviews/<string:event_id>/<string:review_id>", methods=['PUT'])
def update_admin_review(event_id, review_id):
    """
    Update an admin comment for a specific event review.
    ---
    parameters:
        -   in: path
            name: event_id        function fetchReviews(eventId) {
            axios.get(`http://localhost:5001/reviews/${eventId}`)
                .then(response => {
                    const reviews = response.data.data;
                    if (reviews.length === 0) {
                        document.getElementById('reviewsContainer').innerHTML = "<p>No reviews available.</p>";
                        return;
                    }
					let reviewsHtml = '';
					for (let i = 0; i < reviews.length; i++) {
						const review = reviews[i];
						const adminCommentHtml = review.admin_comment ? `<p class="card-text">Admin Comment: ${review.admin_comment}</p>` : '';
						reviewsHtml += `
							<div class="card mb-3">
								<div class="card-body">
									<h5 class="card-title">User ID: ${review.user_id}</h5>
									<p class="card-text">Created At: ${review.created_at}</p>
									<p class="card-text">Rating: ${review.rating}</p>
									<p class="card-text">Comment: ${review.comment}</p>
									${adminCommentHtml}
								</div>
							</div>
						`;
					}
					document.getElementById('reviewsContainer').innerHTML = reviewsHtml;
					})
                .catch(error => {
                    console.error('Error fetching reviews:', error);
                    document.getElementById('reviewsContainer').innerHTML = "<p>Error fetching reviews.</p>";
                });
        }
            required: true
        -   in: path
            name: review_id
            required: true
    requestBody:
        description: Review details
        required: true
        content:
            application/json:
                schema:
                    properties:
                        admin_comment: 
                            type: string
                            description: Admin's comment about the event review

    responses:
        200:
            description: Admin comment for event review updated successfully
        400:
            description: Missing required fields in body. Please provide admin_comment.
        500:
            description: Internal server error

    """
    try:
        required_fields = ['admin_comment']
        if not all(field in request.json for field in required_fields):
            return jsonify(
                {
                    "code": 400,
                    "message": "Missing required fields. Please provide admin_comment."
                }
            ), 400

        doc_ref = db.collection("reviews").document(
            event_id).collection("event_reviews").document(review_id)
        doc_ref.update({
            'admin_comment': request.json['admin_comment']
        })

        return jsonify(
            {
                "code": 200,
                "message": "Admin comment for review updated successfully."
            }
        ), 200
    except Exception as e:
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred while updating the review. " + str(e)
            }
        ), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
