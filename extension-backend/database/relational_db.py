import common.globals as global_vars
from __init__ import conn_cursor
import psycopg2
import uuid

def insert_meeting_info(session_data):
    '''
    Inserts meeting details into relational database
    '''
    meeting_id = str(uuid.uuid4())
    meeting_date = session_data["meeting_date"]
    is_recurring = session_data["meeting_type"] == "recurring"
    transcript_path = f"{meeting_id}_{meeting_date}/transcript.txt"
    output_path = f"{meeting_id}_{meeting_date}/output.docx"

    try:
        sql = "INSERT INTO meeting_details(session_id, meeting_id, meeting_name, meeting_date, is_recurring, transcript_path, output_path) \
                VALUES (%s %s, %s, %s, %s, %s, %s);"
        values = (session_data["session_id"],meeting_id, session_data["meeting_name"], session_data["meeting_date"], is_recurring, transcript_path, output_path)
        conn_cursor.execute(sql, values)
        conn_cursor.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Insert of meeting info into meeting_details table failed", error)

def insert_email(session_id, email):
    '''
    Updates email into relational database
    '''
    try:
        sql = "UPDATE meeting_details SET email=%s WHERE session_id=%s;"
        conn_cursor.execute(sql, (email, session_id))
        conn_cursor.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Insert of email into emails table failed", error)

def fetch_email(session_id):
    '''
    Retrieves email from relational database
    '''
    try:
        sql = "SELECT email from meeting_details WHERE session_id=%s;"
        conn_cursor.execute(sql, (session_id))
        email = conn_cursor.fetchone()[0]
        return email
    except (Exception, psycopg2.DatabaseError) as error:
        print("Select of email from meeting_details table failed", error)
        return None
    

def fetch_meeting_id(session_id):
    '''
    Retrieves meeting_id from relational database
    '''
    try:
        sql = "SELECT meeting_id from meeting_details WHERE session_id=%s;"
        conn_cursor.execute(sql, (session_id))
        meeting_id = conn_cursor.fetchone()[0]
        return meeting_id
    except (Exception, psycopg2.DatabaseError) as error:
        print("Select of meeting_id from meeting_details table failed", error)
        return None
    
def fetch_curr_transcript_path(session_id):
    '''
    Retrieves current meeting transcript path from relational database
    '''
    try:
        sql = "SELECT transcript_path from meeting_details WHERE session_id=%s;"
        conn_cursor.execute(sql, (session_id))
        transcript_path = conn_cursor.fetchone()[0]
        return transcript_path
    except (Exception, psycopg2.DatabaseError) as error:
        print("Select of transcript_path from meeting_details table failed", error)
        return None

# For recurring meetings  
def fetch_prev_transcript_path(meeting_name):
    '''
    Retrieves previous meeting transcript paths from meeting_details table 
    '''
    try:
        sql = "SELECT transcript_path from meeting_details WHERE meeting_name=%s;"
        conn_cursor.execute(sql, (meeting_name))
        transcript_paths = [row[0] for row in conn_cursor.fetchall()]
        return transcript_paths
    except (Exception, psycopg2.DatabaseError) as error:
        print("Select of transcript_paths from meeting_details table failed", error)
        return None

def insert_recording_status(session_id):
    '''
    Inserts recording status into relational database
    '''
    try:
        sql = "INSERT INTO meeting_details(recording_status) VALUES (%s) WHERE session_id=%s;"
        conn_cursor.execute(sql, (True, session_id))
        conn_cursor.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Insert of recording_status into meeting_details table failed", error)

def fetch_recording_status(session_id):
    '''
    Retrieves recording status from relational database
    '''
    try:
        sql = "SELECT recording_status from meeting_details WHERE session_id=%s;"
        conn_cursor.execute(sql, (session_id))
        recording_status = conn_cursor.fetchone()[0]
        return recording_status
    except (Exception, psycopg2.DatabaseError) as error:
        print("Select of recording_status from meeting_details table failed", error)
        return None

def insert_recording_path(session_id, meeting_date):
    '''
    Inserts recording path into relational database
    '''
    global_recording_index = str(global_vars.RECORDING_GLOBAL_INDEX)

    try:
        meeting_id = fetch_meeting_id(session_id)
        recording_path = f"{meeting_id}_{meeting_date}/snippet_{global_recording_index}.webm"

        sql = "INSERT INTO recordings(meeting_id, snippet_recording_path) VALUES (%s, %s);"
        values = (meeting_id, recording_path)
        conn_cursor.execute(sql, values)
        conn_cursor.commit()
        global_vars.RECORDING_GLOBAL_INDEX = global_recording_index + 1
        return recording_path
    except (Exception, psycopg2.DatabaseError) as error:
        print("Insert into recordings table failed", error)
        return None

def insert_image_path(session_id, meeting_date, image_identifier):
    '''
    Inserts image path into relational database
    '''
    try:
        meeting_id = fetch_meeting_id(session_id)
        image_path = f"{meeting_id}_{meeting_date}/{image_identifier}"

        sql = "INSERT INTO images(meeting_id, image_path) VALUES (%s, %s);"
        values = (meeting_id, image_path)
        conn_cursor.execute(sql, values)
        conn_cursor.commit()
    except (Exception, psycopg2.DatabaseError) as error:    
        print("Insert into images table failed", error)

# need to change this to return the latest image path for current meeting so that it can be given as object_name whne uploading to s3
def fetch_image_path(session_id):
    '''
    Retrieves image path from relational database
    '''
    try:
        meeting_id = fetch_meeting_id(session_id)
        sql = "SELECT image_path from images WHERE meeting_id=%s;"
        conn_cursor.execute(sql, (meeting_id))
        image_path = conn_cursor.fetchone()[0]
        return image_path
    except (Exception, psycopg2.DatabaseError) as error:
        print("Select of image_path from images table failed", error)
        return None

def fetch_output_path(session_id):
    '''
    Retrieves current meeting output path from relational database
    '''
    try:
        sql = "SELECT output_path from meeting_details WHERE session_id=%s;"
        conn_cursor.execute(sql, (session_id))
        output_path = conn_cursor.fetchone()[0]
        return output_path
    except (Exception, psycopg2.DatabaseError) as error:
        print("Select of output_path from meeting_details table failed", error)
        return None