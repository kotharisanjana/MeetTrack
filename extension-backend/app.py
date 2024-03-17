from __init__ import initialise
from common.utils import get_date
from database.relational_db import RelationalDb
from src.query_engine import setup_prev_meeting_query_engine, UserInteraction
# from src.realtime_audio import RealtimeAudio
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Initialize objects within the Flask application context
with app.app_context():
  initialise()

@app.route("/meeting_details", methods=["POST"])
def get_meeting_details():
  meeting_name = request.json.get("name")
  meeting_type = request.json.get("meetingType")

  app.config["init_obj"].MEETING_NAME = meeting_name
  app.config["init_obj"].MEETING_DATE = get_date()

  relational_db_obj = RelationalDb()
  app.config["relational_db_obj"] = relational_db_obj

  # insert into relational_db
  relational_db_obj.insert_meeting_info(meeting_type)

  if meeting_type == "recurring":
    setup_prev_meeting_query_engine()

  return jsonify()

@app.route("/record_meeting", methods=["POST"])
def record_meeting():
  # video_file = "" 
  # audio_file = ""
  # RealtimeAudio(video_file, audio_file).realtime_audio_pipeline()
  # insert_recording_status()

  # CHECK WHERE TO CALL THE FUNCTION THAT PUTS THE SNIPPET RECORDING PATH INTO POSTGRES ONCE IT IS UPLOADED TO S3 - insert_recording_snippet_path()
  pass

@app.route("/user_query", methods=["POST"])
def get_query():
  user_query = request.json.get("userInput")
  response = UserInteraction.query_response_pipeline(user_query)
  data = {"response": response}
  return jsonify(data)
  

if __name__ == "__main__":
  app.run(debug=True)
