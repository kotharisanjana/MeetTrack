from common.utils import get_unixtime
import common.globals as global_vars
from __init__ import asr_model
from common.aws_utilities import upload_file_to_s3
import os

class TranscribedText:
  def __init__(self, text):
    self.text = text

class Transcription:
  def __init__(self, start_time, end_time, text):
    self.start_time = start_time
    self.end_time = end_time
    self.text = text 

class ASR:
  def __init__(self, meeting_id):
    self.meeting_id = meeting_id

  def transcribe(self, meeting_audio):
    self.segments, _ = asr_model.transcribe(audio=meeting_audio, language="en")

  def create_transcript(self, transcript_path):
    with open(os.path.join(global_vars.DOWNLOAD_DIR, f"{self.meeting_id}_transcript.txt"), "a") as file:
        for segment in self.segments:
          print(segment.text)
          text = "[ " + str(segment.start) + " -> " + str(segment.end) + " ]" + segment.text + "\n"
          file.write(text)
          file.flush()
        file.write("*" + "\n")
    upload_file_to_s3(os.path.join(global_vars.DOWNLOAD_DIR, f"{self.meeting_id}_transcript.txt"), transcript_path)

  def extract_time(self, time):
    time_str = str(time)
    time_str = time_str.split(".")
    seconds = int(time_str[0])
    hour = seconds//3600
    min = seconds//60
    sec = seconds%60
    millisec = int(time_str[1][:3])
    return hour, min, sec, millisec

  def create_transcript_segments(self):
    self.transcript_segments = []

    for segment in self.segments:
        start = segment.start
        hour, min, sec, millisec = self.extract_time(start)
        start_time = get_unixtime(hour, min, sec, millisec)

        end = segment.end
        hour, min, sec, millisec = self.extract_time(end)
        end_time = get_unixtime(hour, min, sec, millisec)

        # inconsistency in transcription timestamps
        if end_time <= start_time:   # [ 121.24 -> 121.9 ] Thanks, Sam (end time should be 121.90) - handle this in the logic
            continue

        self.transcript_segments.append(Transcription(start_time, end_time, TranscribedText(segment.text)))  