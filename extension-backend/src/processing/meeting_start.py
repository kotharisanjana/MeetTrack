from src.user_interaction.query_engine import PrevMeetingQueryEngine
import common.globals as global_vars
from database.cache import get_redis_client, retrieve_session_data
from database.relational_db import insert_meeting_info, fetch_meeting_id, insert_s3_paths, check_first_occurence
from __init__ import logger

import json
import os

def on_start_processing(session_id):
  session_data = retrieve_session_data(session_id)
  meeting_id = insert_into_relational_db(session_data)
  update_session_data(session_id, meeting_id, session_data)
  create_local_directories(meeting_id)
  setup_prev_meeting_engine(session_data["meeting_type"], meeting_id, session_data["meeting_name"])
  

def insert_into_relational_db(session_data):
  insert_meeting_info(session_data)
  meeting_id = fetch_meeting_id(session_data["session_id"])
  insert_s3_paths(meeting_id)
  return meeting_id


def update_session_data(session_id, meeting_id, session_data):
  redis_client = get_redis_client()

  # update session_data in redis
  session_data["meeting_id"] = meeting_id 
  session_data["local_recording_path"] = os.path.join(global_vars.DOWNLOAD_DIR, f"{meeting_id}/recording/recording.webm")
  session_data["local_audio_path"] = os.path.join(global_vars.DOWNLOAD_DIR, f"{meeting_id}/audio/audio.wav")
  session_data["local_transcript_path"] = os.path.join(global_vars.DOWNLOAD_DIR, f"{meeting_id}/transcript/transcript.txt")
  session_data["local_diarization_path"] = os.path.join(global_vars.DOWNLOAD_DIR, f"{meeting_id}/diarization/diarization.txt")
  session_data["local_output_path"] = os.path.join(global_vars.DOWNLOAD_DIR, f"{meeting_id}/output/output.docx")

  updated_session_json = json.dumps(session_data)
  redis_client.set(session_id, updated_session_json)

  logger.info(f"Updated session data in redis for session_id: {session_id}")


def create_local_directories(meeting_id):
  directory_path = os.path.join(global_vars.DOWNLOAD_DIR, f"{meeting_id}")

  os.makedirs(os.path.join(directory_path, "recording"), exist_ok=True)
  os.makedirs(os.path.join(directory_path, "audio"), exist_ok=True)
  os.makedirs(os.path.join(directory_path, "transcript"), exist_ok=True)
  os.makedirs(os.path.join(directory_path,"output"), exist_ok=True)
  os.makedirs(os.path.join(directory_path, "diarization"), exist_ok=True)
  os.makedirs(os.path.join(directory_path, "prev"), exist_ok=True)

  logger.info(f"Local directories created for meeting_id: {meeting_id}")


def setup_prev_meeting_engine(meeting_type, meeting_id, meeting_name):
  if meeting_type == "recurring":
    # check if this is the first occurence of the recurring meeting
    first_occurence = check_first_occurence(meeting_name, meeting_id)

    # if not first occurence, setup prev_meeting_tool
    if not first_occurence:
      global prev_meeting_tool
      prev_meeting_tool = PrevMeetingQueryEngine(meeting_name, meeting_id).create_query_engine()
      logger.info("Previous meeting query engine setup successful.")
    else:
      logger.info("First occurence of recurring meeting. No previous meeting data available.")