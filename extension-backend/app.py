from realtime_audio import RealtimeAudio
from user_interaction import UserInteraction

from flask import Flask

app = Flask(__name__)

@app.route("/")
def meettrack_main():
    video_file = "" 
    audio_file = ""
    RealtimeAudio(video_file, audio_file).realtime_audio_pipeline()

    # get nearest segments for a query
    query = ""
    response = UserInteraction(query).query_response_pipeline()

    return response

if __name__ == "__main__":
  app.run()
