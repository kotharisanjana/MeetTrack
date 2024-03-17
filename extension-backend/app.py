from __init__ import initialise
from database.relational_db import RelationalDb
from src.query_engine import UserInteraction, setup_prev_meeting_query_engine
from src.realtime_audio import RealtimeAudio
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Initialize objects within the Flask application context
with app.app_context():
  initialise()

def on_submit_meeting_details(meeting_type):
  if app.config.get("meeting_id") is None:
    relational_db_obj = RelationalDb()
    app.config["relational_db_obj"] = relational_db_obj

    # insert into relational_db
    relational_db_obj.insert_meeting_info(meeting_type)
    # get meeting_id from relational_db
    meeting_id = relational_db_obj.get_meeting_id()

    if meeting_type == "recurring":
      setup_prev_meeting_query_engine()
    
    return meeting_id
  else:
    return None


@app.route("/submit-meeting-details", methods=["POST"])
def submit_meeting_details():
  meeting_name = request.json.get("name")
  app.config["meeting_name"] = meeting_name

  meeting_type = request.json.get("meetingType")

  meeting_id = on_submit_meeting_details(meeting_type)
  if meeting_id:
    app.config["meeting_id"] = meeting_id
    return jsonify({"meeting_id": meeting_id})
  else:
    return jsonify({"error": "Ask host for meeting ID to join session."})


@app.route("/start-meeting-session", methods=["POST"])
def start_meeting_session():
  print("communication established")
  return jsonify({"status": "OK"}), 200


@app.route("/join-meeting-session", methods=["POST"])
def join_meeting_session():
  print("inside join-session")
  return jsonify({"status": "OK"}), 200


@app.route("/meeting-recording-status", methods=["POST"])
def meeting_recording_status():
  if app.config["relational_db_obj"].get_recording_status():
    return jsonify({"error": "Recording already in progress."}), 400
  else:
    app.config["relational_db_obj"].insert_recording_status()
    return jsonify({"success": "Recording started successfuly."}), 200
  

@app.route("/process-meeting-recording", methods=["POST"])
def process_meeting_recording():
  if "recording" not in request.files:
    return jsonify({"error": "No recording file provided"}), 400
  
  meeting_recording = request.files["recording"]
  # upload meeting_recording to s3
  app.config["relational_db_obj"].insert_recording_snippet_path()

  RealtimeAudio(meeting_recording).realtime_audio_pipeline()

  return jsonify({"success": "Recording processed successfully"}), 200
  

@app.route("/answer-user-query", methods=["POST"])
def answer_user_query():
  user_query = request.json.get("userInput")
  response = UserInteraction.query_response_pipeline(user_query)
  data = {"response": response}
  return jsonify(data)
  

if __name__ == "__main__":
  app.run(debug=True)
