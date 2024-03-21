from common.utils import get_date
from redis import Redis
import uuid
import json

redis_client = Redis(host="localhost", port=6379, db=0)

def get_redis_client():
    return redis_client

def create_session(meeting_name, meeting_type):
    session_id = str(uuid.uuid4())

    session_data = {
    "session_id": session_id,
    "meeting_name": meeting_name,
    "meeting_date": get_date(),
    "meeting_type": meeting_type,
    }

    # Convert session data to JSON string
    session_json = json.dumps(session_data)

    # Store session data in Redis under session ID key
    redis_client = get_redis_client()
    redis_client.set(session_id, session_json)
    return session_id

def get_session_id(meeting_name):
    redis_client = get_redis_client()
    all_sessions = redis_client.keys('*')

    # Iterate over existing sessions
    for sess_key in all_sessions:
        sess_data = redis_client.get(sess_key)
        sess_dict = json.loads(sess_data)
        if sess_dict.get("meeting_name") == meeting_name and sess_dict.get("meeting_date") == get_date():
            return sess_key.decode('utf-8')
    return None

def retrieve_session_data(session_id):
    redis_client = get_redis_client()
    session_json = redis_client.get(session_id)
    if session_json:
        session_data = json.loads(session_json)
        return session_data
    else:
        return {}