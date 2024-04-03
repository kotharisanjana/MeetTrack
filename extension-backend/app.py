import common.globals as global_vars
from common.aws_utilities import upload_file_to_s3
from common.utils import delete_files
from database.cache import *
from database.relational_db import *
from src.user_interaction.query_engine import UserInteraction, setup_prev_meeting_query_engine
from src.processing.audio_processing import AudioProcessing
from src.processing.image_processing import ImageProcessing
from src.textual.textual_component import TextualComponent
from src.visual.visual_component import VisualComponent
from src.output.final_doc import create_final_doc
from src.output.email import send_email
from flask import Flask, jsonify, request
from flask_session import Session
import json
import os
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

def on_submit_meeting_details(session_id):
  redis_client = get_redis_client()
  session_data = retrieve_session_data(session_id)

  insert_meeting_info(session_data)
  meeting_id = fetch_meeting_id(session_data["session_id"])
  insert_s3_paths(meeting_id)

  # setup previous meeting query engine
  if session_data["meeting_type"] == "recurring":
    first_occurence = check_first_occurence(session_data["meeting_name"], meeting_id)
    if not first_occurence:
      global prev_meeting_tool
      prev_meeting_tool = setup_prev_meeting_query_engine(session_data["meeting_name"], meeting_id)

  # update session_data in redis
  session_data["meeting_id"] = meeting_id 
  session_data["local_recording_path"] = os.path.join(global_vars.DOWNLOAD_DIR, f"{meeting_id}_recording.webm")
  session_data["local_audio_path"] = os.path.join(global_vars.DOWNLOAD_DIR, f"{meeting_id}_audio.wav")
  session_data["local_transcript_path"] = os.path.join(global_vars.DOWNLOAD_DIR, f"{meeting_id}_transcript.txt")
  session_data["local_diarization_path"] = os.path.join(global_vars.DOWNLOAD_DIR, f"{meeting_id}_diarization.txt")
  session_data["local_output_path"] = os.path.join(global_vars.DOWNLOAD_DIR, f"{meeting_id}_output.docx")
  updated_session_json = json.dumps(session_data)
  redis_client.set(session_id, updated_session_json)

  global audio_processing_obj
  audio_processing_obj = AudioProcessing(session_data)

  global image_processing_obj
  image_processing_obj = ImageProcessing(session_data)

  global user_interaction_obj
  user_interaction_obj = UserInteraction(session_data["meeting_id"], session_data["meeting_name"])


@app.route("/submit-details", methods=["POST"])
def submit_details():
  meeting_name = request.json.get("name")
  meeting_type = request.json.get("meetingType")

  session_id = get_session_id(meeting_name)

  if session_id is None:
    session_id = create_session(meeting_name, meeting_type)
    on_submit_meeting_details(session_id)
  
  return jsonify({"status": "OK", "session_id": session_id}), 200


@app.route("/access-session", methods=["POST"])
def access_session():
  session_id = request.json.get("session_id")
  if session_id:
    session_data = retrieve_session_data(session_id)
    if session_data:
        return jsonify({"status": "OK", "message": "You've joined the meeting session!"}), 200
  else:
    return jsonify({"status": "error", "message": "Session ID not provided/ incorrect. Try again"}), 400


@app.route("/submit-recipient-email", methods=["POST"])
def submit_recipient_email():
  email = request.json.get("email")
  session_id = request.json.get("session_id")
  meeting_id = retrieve_session_data(session_id)["meeting_id"]

  insert_email(meeting_id, email)
  return jsonify({"status": "OK", "message": "Recipient email submitted successfully"}), 200


@app.route("/check-recording-status", methods=["POST"])
def check_recording_status():
  session_id = request.json.get("session_id")
  meeting_id = retrieve_session_data(session_id)["meeting_id"]

  if fetch_recording_status(meeting_id):
    return jsonify({"status": "error", "message": "Recording already in progress."}), 400
  else:
    insert_recording_status(meeting_id)
    return jsonify({"status": "OK", "message": "Recording started successfuly."}), 200
  

@app.route("/process-recording", methods=["POST"])
def process_recording():
  if "recording" not in request.files:
    return jsonify({"error": "No recording file provided"}), 400
  
  session_id = request.form.get("session_id")
  meeting_recording = request.files["recording"]

  session_data = retrieve_session_data(session_id)
  meeting_id = session_data["meeting_id"]
  local_recording_path = session_data["local_recording_path"]
  
  meeting_recording.save(local_recording_path)

  # upload meeting recording to s3 and store path in relational database
  recording_path = insert_recording_path(meeting_id)
  upload_file_to_s3(local_recording_path, recording_path)

  audio_processing_obj.online_audio_pipeline() 
  image_processing_obj.online_image_pipeline() 

  return jsonify({"success": "Recording processed successfully"}), 200

  
@app.route("/answer-query", methods=["POST"])
def answer_query():
  user_query = request.json.get("userInput")

  response = user_interaction_obj.query_response_pipeline(prev_meeting_tool, user_query)

  if response:
    return jsonify({"status": "OK", "data": response}), 200
  else:
    return jsonify({"status": "error", "data": "No response found for query. Please try again"}), 400


@app.route("/end-session", methods=["POST"])
def end_session():
  session_id = request.json.get("session_id")
  session_data = retrieve_session_data(session_id)
  meeting_id = session_data["meeting_id"]
  local_transcript_file = session_data["local_transcript_path"]
  
  # generate final transcript with speaker diarization
  audio_processing_obj.offline_audio_pipeline()

  # generate textual component
  textual_component_obj = TextualComponent()
  textual_component = textual_component_obj.textual_component_pipeline(local_transcript_file)
  # extract summary from textual component
  summary = textual_component_obj.extract_summary_from_textual_component(textual_component)

  # image-context and get image links
  if summary:
    image_urls = VisualComponent(meeting_id).get_contextual_images_from_summary(summary)
  else:
    image_urls = []

  # merge into final output doc
  create_final_doc(meeting_id, textual_component, image_urls)

  # email meeting notes to recipient
  send_email(session_data)

  # delete files from local file system
  delete_files(meeting_id)

  # terminate session
  delete_session(session_id)


if __name__ == "__main__":
  app.run(debug=False)