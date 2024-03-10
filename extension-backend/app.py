from init import initialise_objects
# from src.realtime_audio import RealtimeAudio
from src.user_interaction import UserInteraction

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Initialize objects within the Flask application context
with app.app_context():
  initialise_objects()

@app.route("/details", methods=["POST"])
def meeting_details():
  name = request.json.get("name")
  date = request.json.get("date")
  app.config["init_obj"].MEETING_NAME = name
  app.config["init_obj"].MEETING_DATE = date
  return jsonify()

@app.route("/record", methods=["POST"])
def record():
  # video_file = "" 
  # audio_file = ""
  # RealtimeAudio(video_file, audio_file).realtime_audio_pipeline()
  pass

@app.route("/query", methods=["POST"])
def query():
  query = request.json.get("userInput")
  response = UserInteraction(query).query_response_pipeline()
  data = {"response": response}
  return jsonify(data)
  

if __name__ == "__main__":
  app.run(debug=True)
