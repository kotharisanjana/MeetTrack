import common.globals as global_vars
from __init__ import conn_cursor
import psycopg2

# ------------------- Inserts -------------------

def insert_meeting_info(session_data):
    '''
    Inserts meeting details into relational database
    '''
    is_recurring = session_data["meeting_type"] == "recurring"

    try:
        sql = "INSERT INTO meeting_details(session_id, meeting_name, meeting_date, is_recurring) \
                VALUES (%s %s, %s, %s);"
        values = (session_data["session_id"], session_data["meeting_name"], session_data["meeting_date"], is_recurring)
        conn_cursor.execute(sql, values)
        conn_cursor.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error: ", error)


def insert_s3_paths(meeting_id):
    '''
    Inserts S3 paths into relational database
    '''
    try:
        transcript_path = f"{global_vars.TRANSCRIPTION_FOLDER}/{meeting_id}/transcript.txt"
        output_path = f"{global_vars.OUTPUT_FOLDER}/{meeting_id}/output.docx"
        sql = "INSERT INTO s3_paths(meeting_id, transcript_path, output_path) VALUES (%s, %s, %s);"
        values = (meeting_id, transcript_path, output_path)
        conn_cursor.execute(sql, values)
        conn_cursor.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error: ", error)
    

def insert_email(meeting_id, recipient_email):
    '''
    Insert recipient email into relational database
    '''
    try:
        sql = "INSERT INTO email(meeting_id, recipient_email) VALUES (%s, %s);"
        conn_cursor.execute(sql, (meeting_id, recipient_email))
        conn_cursor.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error: ", error)


def insert_recording_status(meeting_id):
    '''
    Inserts recording status into relational database
    '''
    try:
        sql = "INSERT INTO recording_status(meeting_id, status) VALUES (%s) WHERE meeting_id=%s;"
        conn_cursor.execute(sql, (True, meeting_id))
        conn_cursor.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error: ", error)


def insert_recording_path(meeting_id):
    '''
    Inserts recording path into relational database
    '''
    global_recording_index = str(global_vars.RECORDING_GLOBAL_INDEX)

    try:
        recording_path = f"{global_vars.RECORDINGS_FOLDER}/{meeting_id}/snippet_{global_recording_index}.webm"

        sql = "INSERT INTO recordings(meeting_id, recording_path) VALUES (%s, %s);"
        values = (meeting_id, recording_path)
        conn_cursor.execute(sql, values)
        conn_cursor.commit()
        global_vars.RECORDING_GLOBAL_INDEX = global_recording_index + 1
        return recording_path
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error: ", error)
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
        conn_cursor.commit()
    except (Exception, psycopg2.DatabaseError) as error:    
        print("Database error: ", error)

# ------------------- Fetches -------------------
        
def fetch_meeting_id(session_id):
    '''
    Retrieves meeting_id from relational database
    '''
    try:
        sql = "SELECT meeting_id FROM meeting_details WHERE session_id=%s;"
        conn_cursor.execute(sql, (session_id))
        meeting_id = conn_cursor.fetchone()[0]
        return meeting_id
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error: ", error)
        return None
    

def fetch_email(meeting_id):
    '''
    Retrieves email from relational database
    '''
    try:
        sql = "SELECT recipient_email FROM email WHERE meeting_id=%s;"
        conn_cursor.execute(sql, (meeting_id))
        email = conn_cursor.fetchone()[0]
        return email
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error: ", error)
        return None
    

def fetch_curr_transcript_path(meeting_id):
    '''
    Retrieves current meeting transcript path from relational database
    '''
    try:
        sql = "SELECT transcript_path FROM s3_paths WHERE meeting_id=%s;"
        conn_cursor.execute(sql, (meeting_id))
        transcript_path = conn_cursor.fetchone()[0]
        return transcript_path
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error: ", error)
        return None
    

# For recurring meetings  
def fetch_prev_transcript_path(meeting_name):
    '''
    Retrieves previous meeting transcript paths 
    '''
    try:
        sql = "SELECT meeting_id from meeting_details WHERE meeting_name=%s;"
        conn_cursor.execute(sql, (meeting_name))
        prev_meeting_ids = [row[0] for row in conn_cursor.fetchall()]
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error: ", error)

    try:
        sql = "SELECT transcript_path from s3_paths WHERE meeting_id=%s;"
        transcript_paths = []
        for meeting_id in prev_meeting_ids:
            conn_cursor.execute(sql, (meeting_id))
            transcript_paths.append(conn_cursor.fetchone()[0])
        return transcript_paths
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error: ", error)
        return None


def fetch_recording_status(meeting_id):
    '''
    Retrieves recording status from relational database
    '''
    try:
        sql = "SELECT status from recording_status WHERE meeting_id=%s;"
        conn_cursor.execute(sql, (meeting_id))
        status = conn_cursor.fetchone()[0]
        return status
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error: ", error)
        return None


def fetch_output_path(meeting_id):
    '''
    Retrieves current meeting output path from relational database
    '''
    try:
        sql = "SELECT output_path from s3_paths WHERE meeting_id=%s;"
        conn_cursor.execute(sql, (meeting_id))
        output_path = conn_cursor.fetchone()[0]
        return output_path
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error: ", error)
        return None
    

# need to change this to return the latest image path for current meeting so that it can be given as object_name whne uploading to s3
def fetch_image_path(meeting_id):
    '''
    Retrieves image path from relational database
    '''
    try:
        sql = "SELECT image_path from images WHERE meeting_id=%s;"
        conn_cursor.execute(sql, (meeting_id))
        image_path = conn_cursor.fetchone()[0]
        return image_path
    except (Exception, psycopg2.DatabaseError) as error:
        print("Database error: ", error)
        return None