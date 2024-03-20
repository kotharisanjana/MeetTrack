import common.globals as global_vars
import psycopg2
import uuid

class RelationalDb:
    def __init__(self, session_data):
        self.session_data = session_data
        self.conn_cur = session_data["init_obj"].conn_cursor

    def insert_meeting_info(self):
        '''
        Inserts meeting details into relational database
        '''
        meeting_id = str(uuid.uuid4())
        self.meeting_identifier = f"{self.meeting_id}_{self.session_data["meeting_date"]}"
        is_recurring = self.session_data["meeting_type"] == "recurring"
        transcript_path = f"{self.meeting_identifier}/transcript.txt"

        try:
            sql = "INSERT INTO meeting_details(session_id, meeting_id, meeting_name, meeting_date, is_recurring, transcript_path) \
                    VALUES (%s %s, %s, %s, %s, %s);"
            values = (self.session_data["session_id"],meeting_id, self.session_data["meeting_name"], self.session_data["meeting_date"], is_recurring, transcript_path)
            self.conn_cur.execute(sql, values)
            self.conn_cur.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Insert of meeting info into meeting_details table failed", error)

    def fetch_meeting_id(self):
        '''
        Retrieves meeting_id from relational database
        '''
        try:
            sql = "SELECT meeting_id from meeting_details WHERE session_id=%s;"
            self.conn_cur.execute(sql, (self.session_data["session_id"]))
            meeting_id = self.conn_cur.fetchone()[0]
            return meeting_id
        except (Exception, psycopg2.DatabaseError) as error:
            print("Select of meeting_id from meeting_details table failed", error)
            return None
        
    def fetch_curr_transcript_path(self):
        '''
        Retrieves transcript path from relational database
        '''
        try:
            sql = "SELECT transcript_path from meeting_details WHERE session_id=%s;"
            self.conn_cur.execute(sql, (self.session_data["session_id"]))
            transcript_path = self.conn_cur.fetchone()[0]
            return transcript_path
        except (Exception, psycopg2.DatabaseError) as error:
            print("Select of transcript_path from meeting_details table failed", error)
            return None

    # For recurring meetings  
    def fetch_prev_transcript_path(self):
        '''
        Retrieves previous meeting transcript paths from meeting_details table 
        '''
        try:
            sql = "SELECT transcript_path from meeting_details WHERE meeting_name=%s;"
            self.conn_cur.execute(sql, (self.session_data["meeting_name"]))
            transcript_paths = [row[0] for row in self.conn_cur.fetchall()]
            return transcript_paths
        except (Exception, psycopg2.DatabaseError) as error:
            print("Select of transcript_paths from meeting_details table failed", error)
            return None

    def insert_recording_status(self):
        '''
        Inserts recording status into relational database
        '''
        try:
            sql = "INSERT INTO meeting_details(recording_status) VALUES (%s) WHERE session_id=%s;"
            self.conn_cur.execute(sql, (True, self.session_data["session_id"]))
            self.conn_cur.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Insert of recording_status into meeting_details table failed", error)

    def fetch_recording_status(self):
        '''
        Retrieves recording status from relational database
        '''
        try:
            sql = "SELECT recording_status from meeting_details WHERE session_id=%s;"
            self.conn_cur.execute(sql, (self.session_data["session_id"]))
            recording_status = self.conn_cur.fetchone()[0]
            return recording_status
        except (Exception, psycopg2.DatabaseError) as error:
            print("Select of recording_status from meeting_details table failed", error)
            return None

    def insert_recording_path(self):
        '''
        Inserts recording path into relational database
        '''
        global_recording_index = str(global_vars.RECORDING_GLOBAL_INDEX)
        recording_path = f"{self.meeting_identifier}/snippet_{global_recording_index}.webm"

        try:
            meeting_id = self.fetch_meeting_id()
            sql = "INSERT INTO recordings(meeting_id, snippet_recording_path) VALUES (%s, %s);"
            values = (meeting_id, recording_path)
            self.conn_cur.execute(sql, values)
            self.conn_cur.commit()
            global_vars.RECORDING_GLOBAL_INDEX = global_recording_index + 1
            return recording_path
        except (Exception, psycopg2.DatabaseError) as error:
            print("Insert into recordings table failed", error)
            return None

    def insert_image_info(self, desc):
        '''
        Inserts image info into relational database
        '''
        global_image_index = str(global_vars.IMAGE_GLOBAL_INDEX)
        image_path = f"{self.meeting_identifier}/image_{global_image_index}.png"

        try:
            meeting_id = self.fetch_meeting_id()
            sql = "INSERT INTO images(meeting_id, image_path, image_description) VALUES (%s, %s, %s);"
            values = (meeting_id, image_path, desc)
            self.conn_cur.execute(sql, values)
            self.conn_cur.commit()
            global_vars.IMAGE_GLOBAL_INDEX = global_image_index + 1
            return image_path
        except (Exception, psycopg2.DatabaseError) as error:    
            print("Insert into images table failed", error)
            return None