from init import initialise_objects
# from src.realtime_audio import RealtimeAudio
from src.user_query import UserInteraction
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Initialize objects within the Flask application context
with app.app_context():
  initialise_objects()

def setup_prev_meeting_query_engine():
  user_query_obj = UserInteraction()
  app.config["query_obj"] = user_query_obj
  user_query_obj.get_previous_meeting_transcripts()
  user_query_obj.create_tool_prev_meetings()

@app.route("/details", methods=["POST"])
def get_meeting_details():
  name = request.json.get("name")
  date = request.json.get("date")
  app.config["init_obj"].MEETING_NAME = name
  app.config["init_obj"].MEETING_DATE = date
  setup_prev_meeting_query_engine()
  return jsonify()

@app.route("/record", methods=["POST"])
def record_meeting():
  # video_file = "" 
  # audio_file = ""
  # RealtimeAudio(video_file, audio_file).realtime_audio_pipeline()
  pass

@app.route("/query", methods=["POST"])
def get_query():
  user_query = request.json.get("userInput")
  response = app.config["query_obj"].query_response_pipeline(user_query)
  data = {"response": response}
  return jsonify(data)
  

if __name__ == "__main__":
  app.run(debug=True)
