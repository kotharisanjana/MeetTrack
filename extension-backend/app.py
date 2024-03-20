from __init__ import initialise
import common.globals as global_vars
from common.aws_utilities import *
from database.cache import *
from database.relational_db import RelationalDb
from database.vector_db import VectorDb
from src.query_engine import UserInteraction, setup_prev_meeting_query_engine
from src.realtime_audio import RealtimeAudio
from flask import Flask, jsonify, request
from flask_session import Session
import json
from flask_cors import CORS

# Initialize the Flask application
app = Flask(__name__)

# Set the session mechanism details
app.config["SESSION_TYPE"] = global_vars.SESSION_TYPE
app.config["SESSION_REDIS"] = global_vars.SESSION_REDIS
app.config["PERMANENT_SESSION_LIFETIME"] = global_vars.PERMANENT_SESSION_LIFETIME

# Enable CORS
CORS(app)

# Initialize the session mechanism
Session(app)

# Initialize other components 
initialise(app)

# refactor and place in correct file
def on_submit_meeting_details(session_id):
  redis_client = get_redis_client()
  session_data = retrieve_session_data(session_id)

  # initialize vector and relational database objects
  relational_db_obj = RelationalDb(session_data)
  vector_db_obj = VectorDb(session_data)

  # generate meeting_id and insert meeting info into relational database
  relational_db_obj.insert_meeting_info()

  # store database objects in session_data
  session_data["relational_db_obj"] = relational_db_obj
  session_data["vector_db_obj"] = vector_db_obj
  # add meeting_id to session_data
  session_data["meeting_id"] = relational_db_obj.meeting_id  

  # setup previous meeting query engine
  if session_data["meeting_type"] == "recurring":
    prev_meeting_obj = setup_prev_meeting_query_engine(session_data)
    # store previous_meeting_obj in session_data
    session_data["prev_meeting_obj"] = prev_meeting_obj

  # update session_data in redis
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


@app.route("/recording-status", methods=["POST"])
def recording_status():
  session_id = request.json.get("session_id")
  session_data = retrieve_session_data(session_id)

  if session_data["relational_db_obj"].fetch_recording_status():
    return jsonify({"error": "Recording already in progress."}), 400
  else:
    session_data["relational_db_obj"].insert_recording_status()
    return jsonify({"success": "Recording started successfuly."}), 200
  

@app.route("/process-recording", methods=["POST"])
def process_recording():
  if "recording" not in request.files:
    return jsonify({"error": "No recording file provided"}), 400
  
  session_id = request.form.get("session_id")
  meeting_recording = request.files["recording"]

  session_data = retrieve_session_data(session_id)
  
  # upload meeting recording to s3 and store path in relational database
  recording_path = session_data["relational_db_obj"].insert_recording_path()
  if recording_path:
    upload_file_to_s3(session_data["init_obj"].s3_client, meeting_recording, recording_path)

  RealtimeAudio(meeting_recording, session_data).realtime_audio_pipeline()  

  return jsonify({"success": "Recording processed successfully"}), 200

  
@app.route("/answer-query", methods=["POST"])
def answer_query():
  session_id = request.json.get("session_id")
  user_query = request.json.get("userInput")

  response = UserInteraction(session_id).query_response_pipeline(user_query)

  if response:
    data = {"response": response}
    return jsonify({"status": "success", "data": data}), 200
  else:
    return jsonify({"status": "error", "data": "No response found for query. Please try again"}), 400


if __name__ == "__main__":
  app.run(debug=True)
