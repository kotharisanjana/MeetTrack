from init import initialise_objects
# from src.realtime_audio import RealtimeAudio
from src.query_response import UserInteraction
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Initialize objects within the Flask application context
with app.app_context():
  initialise_objects()

def setup_prev_meeting_query_engine():
  query_resp_obj = UserInteraction()
  app.config["query_resp"] = query_resp_obj
  query_resp_obj.get_previous_meeting_transcripts()
  query_resp_obj.create_tool_prev_meetings()

@app.route("/meeting_details", methods=["POST"])
def get_meeting_details():
  name = request.json.get("name")
  meeting_type = request.json.get("meetingType")
  app.config["init_obj"].MEETING_NAME = name
  app.config["init_obj"].MEETING_TYPE = meeting_type
  setup_prev_meeting_query_engine()
  return jsonify()

@app.route("/record_meeting", methods=["POST"])
def record_meeting():
  # video_file = "" 
  # audio_file = ""
  # RealtimeAudio(video_file, audio_file).realtime_audio_pipeline()
  pass

@app.route("/user_query", methods=["POST"])
def get_query():
  user_query = request.json.get("userInput")
  response = app.config["query_resp"].query_response_pipeline(user_query)
  data = {"response": response}
  return jsonify(data)
  

if __name__ == "__main__":
  app.run(debug=True)
