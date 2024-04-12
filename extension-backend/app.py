import common.globals as global_vars
from database.cache import retrieve_session_data, create_session, get_session_id
from database.relational_db import insert_email, fetch_recording_status, insert_recording_status, fetch_email
from src.processing.meeting_start import on_start_processing
from src.processing.meeting_end import on_end_processing
from common.aws_utilities import upload_file_to_s3
from database.relational_db import insert_recording_path, fetch_recording_path
from src.user_interaction.query_engine import UserInteraction
from src.processing.audio_processing import AudioProcessing
from src.processing.image_processing import ImageProcessing

from flask import Flask, jsonify, request
from flask_session import Session
from flask_cors import CORS

# Initialize the Flask application
app = Flask(__name__)

# Set the session mechanism details
app.config["SESSION_TYPE"] = global_vars.SESSION_TYPE
app.config["SESSION_REDIS"] = global_vars.REDIS_SESSION
app.config["PERMANENT_SESSION_LIFETIME"] = global_vars.PERMANENT_SESSION_LIFETIME

# Enable CORS
CORS(app)

# Initialize the session mechanism
Session(app)

prev_meeting_tool = None
audio_processing_obj = None
image_processing_obj = None
user_interaction_obj = None

def save_recording(meeting_recording, meeting_id, local_recording_path):
    # save meeting recording to local file system
    meeting_recording.save(local_recording_path)
    # upload meeting recording to S3 and store path in relational database
    insert_recording_path(meeting_id)
    recording_path = fetch_recording_path(meeting_id)
    upload_file_to_s3(local_recording_path, recording_path)

def init_global_objects(session_data):
  global audio_processing_obj
  audio_processing_obj = AudioProcessing(session_data)

  global image_processing_obj
  image_processing_obj = ImageProcessing(session_data)

  global user_interaction_obj
  user_interaction_obj = UserInteraction(session_data["meeting_name"], session_data["local_transcript_path"])


@app.route("/submit-details", methods=["POST"])
def submit_details():
  try:
    meeting_name = request.json.get("meetingName")
    meeting_type = request.json.get("meetingType")

    if not meeting_name or not meeting_type:
      return jsonify({"message": "Meeting name and type required."}), 400

    session_id = get_session_id(meeting_name)

    if session_id is None:
      # create session if it doesn't exist
      session_id = create_session(meeting_name, meeting_type)
      
      # perform initial steps for providing assistance during meeting
      on_start_processing(session_id)
      session_data = retrieve_session_data(session_id)
      init_global_objects(session_data)

      return jsonify({"message": session_id}), 200
    else:
      return jsonify({"message": "Session already in progress. Enter session ID to access the session."}), 400
  except Exception as e:
        return jsonify({"message": str(e)}), 500
  

@app.route("/access-session", methods=["POST"])
def access_session():
  try:
    session_id = request.json.get("session_id")

    if session_id:
      session_data = retrieve_session_data(session_id)
      if session_data:
          return jsonify({"message": "You've joined the meeting session!"}), 200
      else:
          return jsonify({"message": "Session ID not found. Please enter a valid session ID"}), 400
    else:
      return jsonify({"message": "Session ID not provided. Try again"}), 400
  except Exception as e:
    return jsonify({"message": str(e)}), 500


@app.route("/submit-recipient-email", methods=["POST"])
def submit_recipient_email():
  try:
    email = request.json.get("email")
    session_id = request.json.get("session_id")

    session_data = retrieve_session_data(session_id)
    meeting_id = session_data["meeting_id"]

    insert_email(meeting_id, email)
    return jsonify({"message": "Recipient email submitted successfully"}), 200
  except Exception as e:
    return jsonify({"message": str(e)}), 500


@app.route("/recording-status", methods=["POST"])
def recording_status():
  try:
    session_id = request.json.get("session_id")
    session_data = retrieve_session_data(session_id)
    meeting_id = session_data["meeting_id"]

    # check if recording already in progress
    if fetch_recording_status(meeting_id):
      return jsonify({"message": "Recording already in progress."}), 400
    # if not then insert recording status as True to notify start recording
    else:
      insert_recording_status(meeting_id)
      return jsonify({"message": "Recording started successfuly."}), 200
  except Exception as e:
    return jsonify({"message": str(e)}), 500
  

@app.route("/process-recording", methods=["POST"])
def process_recording():
  try:
    if "recording" not in request.files:
      return jsonify({"error": "Recording unavailable."}), 400
    
    session_id = request.form.get("session_id")
    meeting_recording = request.files["recording"]

    session_data = retrieve_session_data(session_id)
    meeting_id = session_data["meeting_id"]
    local_recording_path = session_data["local_recording_path"] 

    save_recording(meeting_recording, meeting_id, local_recording_path)
    audio_processing_obj.online_audio_pipeline() 
    image_processing_obj.online_image_pipeline()

    return jsonify({"message": "Recording processed successfully."}), 200
  except Exception as e:
    return jsonify({"message": str(e)}), 500

  
@app.route("/answer-query", methods=["POST"])
def answer_query():
  try:
    user_query = request.json.get("userInput")

    if user_query is None:
      return jsonify({"message": "User query not provided"}), 400

    # get response to user query
    response = user_interaction_obj.query_response_pipeline(prev_meeting_tool, user_query)

    if response:
      return jsonify({"message": response}), 200
    else:
      return jsonify({"message": "Sorry, I am unable to answer your query at the moment. Please try again later."}), 400
  except Exception as e:
    return jsonify({"message": str(e)}), 500


@app.route("/end-session", methods=["POST"])
def end_session():
  try:
    session_id = request.json.get("session_id")

    session_data = retrieve_session_data(session_id)
    meeting_id = session_data["meeting_id"]

    recipient_email = fetch_email(meeting_id)

    if recipient_email is None:
      return jsonify({"message": "Recipient email not found. Please submit recipient email before ending session"}), 400

    # processing on meeting end
    audio_processing_obj.offline_audio_pipeline()
    on_end_processing(session_data)

    return jsonify({"status": "OK", "message": "Recipient will receive meeting notes shortly. Thank you for using MeetTrack"}), 200
  except Exception as e:
    return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
  app.run(debug=False)