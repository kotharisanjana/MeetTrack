from common.utils import get_date
from __init__ import redis_client, logger

import uuid
import json

def get_redis_client():
    """
    Get the Redis client.

    :return: Redis client
    """
    return redis_client


def create_session(meeting_name, meeting_type):
    """
    Create a new session.
    
    :param meeting_name: Name of the meeting
    :param meeting_type: Type of the meeting
    :return: Session ID
    """
    session_id = str(uuid.uuid4())

    session_data = {
        "session_id": session_id,
        "meeting_name": meeting_name,
        "meeting_date": get_date().strftime("%Y-%m-%d"),
        "meeting_type": meeting_type,
    }

    # Convert session data to JSON string
    session_json = json.dumps(session_data)

    # Store session data in Redis under session ID key
    redis_client = get_redis_client()
    redis_client.set(session_id, session_json)
    logger.info(f"Session {session_id} created successfully")

    return session_id


def get_session_id(meeting_name):
    """
    Get the session ID for an existing session.

    :param meeting_name: Name of the meeting
    :return: Session ID if session exists, else None
    """
    redis_client = get_redis_client()
    all_sessions = redis_client.keys('*')

    # Iterate over existing sessions
    for sess_key in all_sessions:
        sess_data = redis_client.get(sess_key)
        sess_dict = json.loads(sess_data)

        # if the meeting name and date match, return the session ID
        if sess_dict.get("meeting_name") == meeting_name and sess_dict.get("meeting_date") == get_date():
            return sess_key.decode('utf-8')
        
    return None


def retrieve_session_data(session_id):
    """
    Retrieve session data from Redis.
    
    :param session_id: Session ID
    :return: Session data if session exists, else empty dictionary
    """
    redis_client = get_redis_client()
    session_json = redis_client.get(session_id)

    if session_json:
        session_data = json.loads(session_json)
        return session_data
    else:
        return {}
    

def delete_session(session_id):
    """
    Delete a session from Redis.
    
    :param session_id: Session ID
    """
    redis_client = get_redis_client()
    redis_client.delete(session_id)
    logger.info(f"Session {session_id} deleted successfully")