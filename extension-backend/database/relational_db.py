import common.globals as global_vars
from __init__ import conn_cursor
import psycopg2.extras
from datetime import datetime
import uuid

# ------------------- Inserts -------------------
psycopg2.extras.register_uuid()

def insert_meeting_info(session_data):
    '''
    Inserts meeting details into relational database
    '''
    is_recurring = session_data["meeting_type"] == "recurring"
    meeting_date = datetime.strptime(session_data["meeting_date"], '%Y-%m-%d').date()
    session_id = uuid.UUID(session_data["session_id"])

    try:
        sql = "INSERT INTO meeting_details(session_id, meeting_name, meeting_date, is_recurring) \
                VALUES (%s, %s, %s, %s);"
        values = (session_id, session_data["meeting_name"], meeting_date, is_recurring)
        conn_cursor.execute(sql, values)
        conn_cursor.connection.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error in insert_meeting_info(): ", error)


def insert_s3_paths(meeting_id):
    '''
    Inserts S3 paths into relational database
    '''
    transcript_path = f"{global_vars.TRANSCRIPTION_FOLDER}/{meeting_id}_transcript.txt"
    output_path = f"{global_vars.OUTPUT_FOLDER}/{meeting_id}_output.docx"
    
    try:
        sql = "INSERT INTO s3_paths(meeting_id, transcript_path, output_path) VALUES (%s, %s, %s);"
        values = (meeting_id, transcript_path, output_path)
        conn_cursor.execute(sql, values)
        conn_cursor.connection.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error in insert s3_paths(): ", error)
    

def insert_email(meeting_id, recipient_email):
    '''
    Insert recipient email into relational database
    '''
    try:
        sql = "INSERT INTO email(meeting_id, recipient_email) VALUES (%s, %s);"
        conn_cursor.execute(sql, (meeting_id, recipient_email))
        conn_cursor.connection.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error in insert_email(): ", error)


def insert_recording_status(meeting_id):
    '''
    Inserts recording status into relational database
    '''
    try:
        sql = "INSERT INTO recording_status(meeting_id, status) VALUES (%s, %s);"
        conn_cursor.execute(sql, (meeting_id, True, ))
        conn_cursor.connection.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error in insert_recording_status(): ", error)


def insert_recording_path(meeting_id):
    '''
    Inserts recording path into relational database
    '''
    global_recording_index = str(global_vars.RECORDING_GLOBAL_INDEX)

    try:
        recording_path = f"{global_vars.RECORDINGS_FOLDER}/{str(meeting_id)}_snippet_{global_recording_index}.webm"

        sql = "INSERT INTO recordings(meeting_id, recording_path) VALUES (%s, %s);"
        values = (meeting_id, recording_path)
        conn_cursor.execute(sql, values)
        conn_cursor.connection.commit()
        global_vars.RECORDING_GLOBAL_INDEX = global_vars.RECORDING_GLOBAL_INDEX + 1
        return recording_path
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error in insert_recording_path(): ", error)
        return None
    

def insert_image_path(meeting_id, image_identifier):
    '''
    Inserts image path into relational database
    '''
    try:
        image_path = f"{global_vars.SCREENSHOTS_FOLDER}/{meeting_id}/{image_identifier}"

        sql = "INSERT INTO images(meeting_id, image_path) VALUES (%s, %s);"
        values = (meeting_id, image_path)
        conn_cursor.execute(sql, values)
        conn_cursor.connection.commit()
    except (Exception, psycopg2.DatabaseError) as error:    
        print("Database error in insert_image_path(): ", error)

# ------------------- Fetches -------------------
        
def fetch_meeting_id(session_id):
    '''
    Retrieves meeting_id from relational database
    '''
    try:
        sql = "SELECT meeting_id FROM meeting_details WHERE session_id::text=%s;"
        conn_cursor.execute(sql, (session_id, ))
        meeting_id = conn_cursor.fetchone()[0]
        return meeting_id
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error in fetch_meeting_id(): ", error)
        return None
    

def fetch_email(meeting_id):
    '''
    Retrieves email from relational database
    '''
    try:
        sql = "SELECT recipient_email FROM email WHERE meeting_id=%s;"
        conn_cursor.execute(sql, (meeting_id, ))
        email = conn_cursor.fetchone()[0]
        return email
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error in fetch_email(): ", error)
        return None
    

def fetch_curr_transcript_path(meeting_id):
    '''
    Retrieves current meeting transcript path from relational database
    '''
    try:
        sql = "SELECT transcript_path FROM s3_paths WHERE meeting_id=%s;"
        conn_cursor.execute(sql, (meeting_id, ))
        transcript_path = conn_cursor.fetchone()[0]
        return transcript_path
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error in fetch_curr_transcript_path(): ", error)
        return None
    

# For recurring meetings  
def fetch_prev_transcript_path(meeting_name, meeting_id):
    '''
    Retrieves previous meeting transcript paths 
    '''
    prev_meeting_ids = []

    try:
        sql = "SELECT meeting_id from meeting_details WHERE meeting_name=%s and meeting_id<>%s;"
        conn_cursor.execute(sql, (meeting_name, meeting_id))
        prev_meeting_ids = [row[0] for row in conn_cursor.fetchall()]
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error in fetch_prev_transcript_path() meeting_id: ", error)

    if prev_meeting_ids:
        try:
            sql = "SELECT transcript_path from s3_paths WHERE meeting_id=%s;"
            transcript_paths = []
            for meeting_id in prev_meeting_ids:
                conn_cursor.execute(sql, (meeting_id, ))
                transcript_paths.append(conn_cursor.fetchone()[0])
            return transcript_paths
        except (Exception, psycopg2.DatabaseError) as error:
            print("Database error in fetch_prev_transcript_path(): ", error)
            return None


def fetch_recording_status(meeting_id):
    '''
    Retrieves recording status from relational database
    '''
    try:
        sql = "SELECT status from recording_status WHERE meeting_id=%s;"
        conn_cursor.execute(sql, (meeting_id, ))
        status = conn_cursor.fetchone()
        if status:
            return status[0]
        else:
            return None
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error in fetch_recording_status(): ", error)
        return None


def fetch_output_path(meeting_id):
    '''
    Retrieves current meeting output path from relational database
    '''
    try:
        sql = "SELECT output_path from s3_paths WHERE meeting_id=%s;"
        conn_cursor.execute(sql, (meeting_id, ))
        output_path = conn_cursor.fetchone()[0]
        return output_path
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error in fetch_output_path(): ", error)
        return None
    

# need to change this to return the latest image path for current meeting so that it can be given as object_name whne uploading to s3
def fetch_image_path(meeting_id):
    '''
    Retrieves image path from relational database
    '''
    try:
        sql = "SELECT image_path from images WHERE meeting_id=%s;"
        conn_cursor.execute(sql, (meeting_id, ))
        image_path = conn_cursor.fetchone()[0]
        return image_path
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error in fetch_image_path(): ", error)
        return None
    
# -------------------------------Querying--------------------------------
def check_first_occurence(meeting_name, meeting_id):
    '''
    Checks if the meeting is the first occurence of a recurring meeting
    '''
    try:
        sql = "SELECT meeting_id FROM meeting_details WHERE meeting_name=%s and meeting_id<>%s;"
        conn_cursor.execute(sql, (meeting_name, meeting_id))
        first_occurence = conn_cursor.fetchone()
        if first_occurence is None:
            return True
        return False
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error in check_first_occurence(): ", error)
        return None