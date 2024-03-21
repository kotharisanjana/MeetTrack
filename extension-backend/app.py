import common.globals as global_vars
from common.aws_utilities import *
from database.cache import *
from database.relational_db import *
from src.query_engine import UserInteraction, setup_prev_meeting_query_engine
from src.realtime_processing import RealtimeAudio
from src.textual_component import TextualComponent
from src.output import create_final_doc
from src.email import send_email
from flask import Flask, jsonify, request
from flask_session import Session
import json
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

# refactor and place in correct file
def on_submit_meeting_details(session_id):
  redis_client = get_redis_client()
  session_data = retrieve_session_data(session_id)

  insert_meeting_info(session_data)

  # setup previous meeting query engine
  if session_data["meeting_type"] == "recurring":
    prev_meeting_tool = setup_prev_meeting_query_engine(session_data["meeting_name"])

   # update session_data in redis
  session_data["prev_meeting_tool"] = prev_meeting_tool
  session_data["meeting_id"] = fetch_meeting_id(session_id) 
  updated_session_json = json.dumps(session_data)
  redis_client.set(session_id, updated_session_json)


@app.route("/submit-details", methods=["POST"])
def submit_details():
  meeting_name = request.json.get("name")
  meeting_type = request.json.get("meetingType")

  session_id = get_session_id(meeting_name)

  if session_id is None:
    session_id = create_session(meeting_name, meeting_type)
    on_submit_meeting_details(session_id)
  
  return jsonify({"session_id": session_id, "status": "OK"}), 200


@app.route("/access-session", methods=["POST"])
def access_session():
  session_id = request.json.get("session_id")
  if session_id:
    session_data = retrieve_session_data(session_id)
    if session_data:
        return jsonify({"status": "success", "message": "You've joined the meeting session!"}), 200
  else:
    return jsonify({"status": "error", "message": "Session ID not provided/ incorrect. Try again"}), 400


@app.route("/submit-recipient-email", methods=["POST"])
def submit_recipient_email():
  email = request.json.get("email")
  session_id = request.json.get("session_id")
  insert_email(session_id, email)
  return jsonify({"status": "success", "message": "Recipient email submitted successfully"}), 200


@app.route("/recording-status", methods=["POST"])
def recording_status():
  session_id = request.json.get("session_id")

  if fetch_recording_status(session_id):
    return jsonify({"error": "Recording already in progress."}), 400
  else:
    insert_recording_status(session_id)
    return jsonify({"success": "Recording started successfuly."}), 200
  

@app.route("/process-recording", methods=["POST"])
def process_recording():
  if "recording" not in request.files:
    return jsonify({"error": "No recording file provided"}), 400
  
  session_id = request.form.get("session_id")
  meeting_date = retrieve_session_data(session_id)["meeting_date"]
  meeting_recording = request.files["recording"]
  
  # upload meeting recording to s3 and store path in relational database
  recording_path = insert_recording_path(session_id, meeting_date)
  if recording_path:
    upload_file_to_s3(meeting_recording, recording_path)

  RealtimeAudio(meeting_recording).realtime_audio_pipeline()  

  return jsonify({"success": "Recording processed successfully"}), 200

  
@app.route("/answer-query", methods=["POST"])
def answer_query():
  session_id = request.json.get("session_id")
  user_query = request.json.get("userInput")

  session_data = retrieve_session_data(session_id)
  meeting_name = session_data["meeting_name"]
  prev_meeting_tool = session_data["prev_meeting_tool"]

  response = UserInteraction(session_id, meeting_name).query_response_pipeline(user_query, prev_meeting_tool)

  if response:
    data = {"response": response}
    return jsonify({"status": "success", "data": data}), 200
  else:
    return jsonify({"status": "error", "data": "No response found for query. Please try again"}), 400


# this should create all textual components, create meeting notes doc by combining text and images, and dispose all resources
@app.route("/processing-after-tab-close", methods=["POST"])
def processing_after_tab_close():
  session_id = request.json.get("session_id")
  session_data = retrieve_session_data(session_id)
  meeting_name = session_data["meeting_name"]
  meeting_date = session_data["meeting_date"]

  recipient_email = fetch_email(session_id)
  
  textual_component = TextualComponent(session_id).textual_component_pipeline()
  output_path = fetch_output_path(session_id)
  create_final_doc(textual_component, image_keys, output_path)
  send_email(output_path, local_file_path, recipient_email, meeting_name, meeting_date)
  pass


if __name__ == "__main__":
  app.run(debug=True)
