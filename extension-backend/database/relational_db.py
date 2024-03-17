import common.globals as g
from flask import current_app
import psycopg2

class RelationalDb:
    def __init__(self):
        self.conn_cur = current_app["init_obj"].conn_cursor
        self.meeting_name = current_app["init_obj"].MEETING_NAME
        self.meeting_date = current_app["init_obj"].MEETING_DATE
        self.meeting_identifier = f"{self.meeting_name.replace(" ", "_")}_{self.meeting_date}/"

    def insert_meeting_info(self, meeting_type):
        '''
        Inserts meeting details into relational database
        '''

        is_recurring = meeting_type == "recurring"

        s3_path = f"{g.S3_BUCKET}/{self.meeting_identifier}"
        transcript_path = f"{self.meeting_identifier}/transcript.txt"
        output_path = f"{self.meeting_identifier}/output.txt"

        try:
            sql = "INSERT INTO meeting_details(meeting_name, meeting_date, is_recurring, s3_path, transcript_path, output_path) \
                    VALUES (%s, %s, %s, %s, %s, %s);"
            values = (self.meeting_name, self.meeting_date, is_recurring, s3_path, transcript_path, output_path)
            
            self.conn_cur.execute(sql, values)
            self.conn_cur.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Insert of meeting info into meeting_details table failed", error)


    def insert_recording_status(self):
        '''
        Inserts recording status into relational database
        '''

        try:
            sql = "INSERT INTO meeting_details(recording_status) VALUES (%s) WHERE meeting_name=%s AND meeting_date=%s;"
            
            self.conn_cur.execute(sql, (True, self.meeting_name, self.meeting_date))
            self.conn_cur.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Insert of recording_status into meeting_details table failed", error)


    def get_meeting_id(self):
        '''
        Retrieves meeting id from relational database
        '''

        try:
            sql = "SELECT meeting_id from meeting_details WHERE meeting_name=%s AND meeting_date=%s;"
            self.conn_cur.execute(sql, (self.meeting_name, self.meeting_date))
            
            meeting_id = self.conn_cur.fetchone()[0]
        except (Exception, psycopg2.DatabaseError) as error:
            print("Select of meeting_id from meeting_details table failed", error)

        return meeting_id


    def insert_recording_snippet_path(self):
        '''
        Inserts recording snippet path into relational database
        '''

        global_recording_snippet_index = g.RECORDING_SNIPPET_GLOBAL_INDEX
        snippet_path = f"{self.meeting_identifier}/snippet_{global_recording_snippet_index}.webm"

        meeting_id = self.get_meeting_id()

        try:
            sql = "INSERT INTO recordings(meeting_id, snippet_recording_path) VALUES (%s, %s);"
            values = (meeting_id, snippet_path)
            
            self.conn_cur.execute(sql, values)
            self.conn_cur.commit()
            
            g.RECORDING_SNIPPET_GLOBAL_INDEX = global_recording_snippet_index + 1
        except (Exception, psycopg2.DatabaseError) as error:
            print("Insert into recordings table failed", error)


    def insert_image_info(self, desc):
        '''
        Inserts image info into relational database
        '''

        global_image_index = g.IMAGE_GLOBAL_INDEX
        image_path = f"{self.meeting_identifier}/image_{global_image_index}.png"

        meeting_id = self.get_meeting_id()

        try:
            sql = "INSERT INTO images(meeting_id, image_path, image_description) VALUES (%s, %s, %s);"
            values = (meeting_id, image_path, desc)
            
            self.conn_cur.execute(sql, values)
            self.conn_cur.commit()
            
            g.IMAGE_GLOBAL_INDEX = global_image_index + 1
        except (Exception, psycopg2.DatabaseError) as error:    
            print("Insert into images table failed", error)


    def get_prev_meeting_transcript(self):
        '''
        Retrieves previous meeting transcript paths from meeting_details table 
        '''
        try:
            sql = "SELECT transcript_path from meeting_details WHERE meeting_name=%s;"
            self.conn_cur.execute(sql, (self.meeting_name))
            
            transcript_paths = [row[0] for row in self.conn_cur.fetchall()]
            return transcript_paths
        except (Exception, psycopg2.DatabaseError) as error:
            print("Select of transcript_paths from meeting_details table failed", error)

        return None


    def get_curr_meeting_transcript(self):
        '''
        Retrieves current meeting transcript path from meeting_details table
        '''
        
        try:
            sql = "SELECT transcript_path from meeting_details WHERE meeting_name=%s AND meeting_date=%s;"
            self.conn_cur.execute(sql, (self.meeting_name, self.meeting_date))
            
            transcript_path = [self.conn_cur.fetchone()[0]]
            return transcript_path
        except (Exception, psycopg2.DatabaseError) as error:
            print("Select of transcript_path from meeting_details table failed", error)

        return None