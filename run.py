from realtime_audio import RealtimeAudio
from query import QueryResponse

# realtime audio pipeline - call everytime new video segment is pushed in s3
# set identifiers for these files
video_file = "" 
audio_file = ""
realtime_audio_obj = RealtimeAudio(video_file, audio_file)
realtime_audio_obj.realtime_audio_pipeline()

# get nearest segments for a query
query = ""
query_response_obj = QueryResponse(query)
responses = query_response_obj.query_pipeline()
