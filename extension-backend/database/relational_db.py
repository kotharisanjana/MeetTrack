import common.globals as global_vars
from __init__ import conn_cursor, logger

import psycopg2.extras
from datetime import datetime
import uuid

psycopg2.extras.register_uuid()

# ------------------- Inserts -------------------

def insert_meeting_info(session_data):
    """
    Insert meeting details into relational database.
    
    :param session_data: Meeting details
    :return: True if successful, False otherwise
    """
    is_recurring = session_data["meeting_type"] == "recurring"
    meeting_date = datetime.strptime(session_data["meeting_date"], '%Y-%m-%d').date()
    session_id = uuid.UUID(session_data["session_id"])

    try:
        sql = "INSERT INTO meeting_details(session_id, meeting_name, meeting_date, is_recurring) \
                VALUES (%s, %s, %s, %s);"
        values = (session_id, session_data["meeting_name"], meeting_date, is_recurring)
        conn_cursor.execute(sql, values)
        conn_cursor.connection.commit()

        logger.info("Meeting details inserted successfully")
        return True
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error in insert_meeting_info(): {error}")
        return False
    

def insert_s3_paths(meeting_id):
    """
    Insert S3 paths into relational database.
    
    :param meeting_id: ID of the meeting
    :return: True if successful, False otherwise
    """
    transcript_path = f"{global_vars.TRANSCRIPTION_FOLDER}/{meeting_id}_transcript.txt"
    output_path = f"{global_vars.OUTPUT_FOLDER}/{meeting_id}_output.docx"
    diarization_path = f"{global_vars.DIARIZATION_FOLDER}/{meeting_id}_diarization.txt"
    
    try:
        sql = "INSERT INTO s3_paths(meeting_id, transcript_path, diarization_path, output_path) VALUES (%s, %s, %s, %s);"
        values = (meeting_id, transcript_path, diarization_path, output_path)
        conn_cursor.execute(sql, values)
        conn_cursor.connection.commit()

        logger.info("S3 paths inserted successfully")
        return True
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error in insert_s3_paths(): {error}")
        return False
    

def insert_email(meeting_id, recipient_email):
    """
    Insert recipient email into relational database.
    
    :param meeting_id: ID of the meeting
    :param recipient_email: Email of the recipient
    :return: True if successful, False otherwise
    """
    try:
        sql = "INSERT INTO email(meeting_id, recipient_email) VALUES (%s, %s);"
        conn_cursor.execute(sql, (meeting_id, recipient_email))
        conn_cursor.connection.commit()

        logger.info("Email inserted successfully")
        return True
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error in insert_email(): {error}")
        return False


def insert_recording_status(meeting_id):
    """
    Insert recording status into relational database.
    
    :param meeting_id: ID of the meeting
    :return: True if successful, False otherwise
    """
    try:
        sql = "INSERT INTO recording_status(meeting_id, status) VALUES (%s, %s);"
        conn_cursor.execute(sql, (meeting_id, True, ))
        conn_cursor.connection.commit()

        logger.info("Recording status inserted successfully")
        return True
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error in insert_recording_status(): {error}")
        return False


def insert_recording_path(meeting_id):
    """
    Insert recording path into relational database.
    
    :param meeting_id: ID of the meeting
    :return: True if successful, False otherwise
    """
    global_recording_index = str(global_vars.RECORDING_GLOBAL_INDEX)
    recording_path = f"{global_vars.RECORDINGS_FOLDER}/{str(meeting_id)}_snippet_{global_recording_index}.webm"

    try:
        sql = "INSERT INTO recordings(meeting_id, recording_path) VALUES (%s, %s);"
        values = (meeting_id, recording_path)
        conn_cursor.execute(sql, values)
        conn_cursor.connection.commit()

        global_vars.RECORDING_GLOBAL_INDEX = global_vars.RECORDING_GLOBAL_INDEX + 1

        logger.info("Recording path inserted successfully")
        return True
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error in insert_recording_path(): {error}")
        return False
    

def insert_image_path(meeting_id, image_path):
    """
    Insert image path into relational database.
    
    :param meeting_id: ID of the meeting
    :param image_path: Path of the image
    :return: True if successful, False otherwise
    """
    try:
        sql = "INSERT INTO images(meeting_id, image_path) VALUES (%s, %s);"
        values = (meeting_id, image_path)
        conn_cursor.execute(sql, values)
        conn_cursor.connection.commit()

        logger.info("Image path inserted successfully")
        return True
    except (Exception, psycopg2.DatabaseError) as error:    
        logger.error(f"Error in insert_image_path(): {error}")
        return False
    

# ------------------- Fetches -------------------
        
def fetch_meeting_id(session_id):
    """
    Retrieves meeting ID from relational database.
    
    :param session_id: ID of the session
    :return: Meeting ID if successful, None otherwise
    """
    try:
        sql = "SELECT meeting_id FROM meeting_details WHERE session_id::text=%s;"
        conn_cursor.execute(sql, (session_id, ))
        meeting_id = conn_cursor.fetchone()[0]

        logger.info("Meeting ID fetched successfully")
        return meeting_id
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error in fetch_meeting_id(): {error}")
        return None
    

def fetch_recording_path(meeting_id):
    """
    Retrieves recording path from relational database.
    
    :param meeting_id: ID of the meeting
    :return: Recording path if successful, None otherwise
    """
    try:
        sql = "SELECT recording_path FROM recordings WHERE meeting_id=%s;"
        conn_cursor.execute(sql, (meeting_id, ))
        recording_path = conn_cursor.fetchone()[0]

        logger.info("Recording path fetched successfully")
        return recording_path
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error in fetch_recording_path(): {error}")
        return None
    

def fetch_email(meeting_id):
    """
    Retrieves recipient email from relational database.
    
    :param meeting_id: ID of the meeting
    :return: Recipient email if successful, None otherwise
    """
    try:
        sql = "SELECT recipient_email FROM email WHERE meeting_id=%s;"
        conn_cursor.execute(sql, (meeting_id, ))
        email = conn_cursor.fetchone()[0]

        logger.info("Email fetched successfully")
        return email
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error in fetch_email(): {error}")
        return None
    

def fetch_curr_transcript_path(meeting_id):
    """
    Retrieves current meeting transcript path from relational database.
    
    :param meeting_id: ID of the meeting
    :return: Transcript path if successful, None otherwise
    """
    try:
        sql = "SELECT transcript_path FROM s3_paths WHERE meeting_id=%s;"
        conn_cursor.execute(sql, (meeting_id, ))
        transcript_path = conn_cursor.fetchone()[0]

        logger.info("Transcript path fetched successfully")
        return transcript_path
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error in fetch_curr_transcript_path(): {error}")
        return None


def fetch_diarization_path(meeting_id):
    """
    Retrieves diarization path from relational database.
    
    :param meeting_id: ID of the meeting
    :return: Diarization path if successful, None otherwise
    """
    try:
        sql = "SELECT diarization_path FROM s3_paths WHERE meeting_id=%s;"
        conn_cursor.execute(sql, (meeting_id, ))
        diarization_path = conn_cursor.fetchone()[0]

        logger.info("Diarization path fetched successfully")
        return diarization_path
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error in fetch_diarization_path(): {error}")
        return None
    

# For recurring meetings  
def fetch_prev_transcript_path(meeting_name, meeting_id):
    """
    Retrieves previous meeting transcript paths from relational database.
    
    :param meeting_name: Name of the meeting
    :param meeting_id: ID of the meeting
    :return: List of previous meeting transcript paths if successful, None otherwise
    """
    prev_meeting_ids = []

    try:
        sql = "SELECT meeting_id from meeting_details WHERE meeting_name=%s and meeting_id<>%s;"
        conn_cursor.execute(sql, (meeting_name, meeting_id))
        prev_meeting_ids = [row[0] for row in conn_cursor.fetchall()]
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error in fetch_prev_transcript_path() while fetching meeting_ids: {error}")

    if prev_meeting_ids:
        try:
            sql = "SELECT transcript_path from s3_paths WHERE meeting_id=%s;"
            transcript_paths = []
            for meeting_id in prev_meeting_ids:
                conn_cursor.execute(sql, (meeting_id, ))
                transcript_paths.append(conn_cursor.fetchone()[0])

            logger.info("Previous transcript paths fetched successfully")
            return transcript_paths
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(f"Error in fetch_prev_transcript_path() while fetching transcript_paths: {error}")
            return None


def fetch_recording_status(meeting_id):
    """
    Retrieves recording status from relational database.
    
    :param meeting_id: ID of the meeting
    :return: True if successful, False if status does not exist, None otherwise
    """
    try:
        sql = "SELECT status from recording_status WHERE meeting_id=%s;"
        conn_cursor.execute(sql, (meeting_id, ))
        status = conn_cursor.fetchone()[0]

        if status:
            logger.info("Recording status fetched successfully")
            return True
        else:
            logger.info("Recording status does not exist")
            return False
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error in fetch_recording_status(): {error}")
        return None


def fetch_output_path(meeting_id):
    """
    Retrieves output path from relational database.
    
    :param meeting_id: ID of the meeting
    :return: Output path if successful, None otherwise
    """
    try:
        sql = "SELECT output_path from s3_paths WHERE meeting_id=%s;"
        conn_cursor.execute(sql, (meeting_id, ))
        output_path = conn_cursor.fetchone()[0]

        logger.info("Output path fetched successfully")
        return output_path
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error in fetch_output_path(): {error}")  
        return None
    

def fetch_image_path(meeting_id):
    """
    Retrieves image paths from relational database.
    
    :param meeting_id: ID of the meeting
    :return: List of image paths if successful, None otherwise
    """
    try:
        sql = "SELECT image_path from images WHERE meeting_id=%s;"
        conn_cursor.execute(sql, (meeting_id, ))
        image_paths = [row[0] for row in conn_cursor.fetchall()]

        logger.info("Image paths fetched successfully")
        return image_paths
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error in fetch_image_path(): {error}")
        return None
    

# -------------------------------Querying--------------------------------
def check_first_occurence(meeting_name, meeting_id):
    """
    Check if the meeting is the first occurence of a recurring meeting.
    
    :param meeting_name: Name of the meeting
    :param meeting_id: ID of the meeting
    :return: True if first occurence, False otherwise, None if error
    """
    try:
        sql = "SELECT meeting_id FROM meeting_details WHERE meeting_name=%s and meeting_id<>%s;"
        conn_cursor.execute(sql, (meeting_name, meeting_id))
        first_occurence = conn_cursor.fetchone()[0]
        if first_occurence is None:
            logger.info("First occurence of recurring meeting")
            return True
        else:
            logger.info("Not the first occurence of recurring meeting")
            return False
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error in check_first_occurence(): {error}")
        return None