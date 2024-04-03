from common.utils import get_unixtime
from __init__ import asr_model
from common.aws_utilities import upload_file_to_s3

class TranscribedText:
  def __init__(self, text):
    self.text = text

class Transcription:
  def __init__(self, start_time, end_time, text):
    self.start_time = start_time
    self.end_time = end_time
    self.text = text 

class ASR:
  def __init__(self, meeting_id, local_transcript_path):
    self.meeting_id = meeting_id
    self.local_transcript_path = local_transcript_path

  def transcribe(self, meeting_audio):
    self.segments, _ = asr_model.transcribe(audio=meeting_audio, language="en")

  def create_transcript(self, transcript_path):
    with open(self.local_transcript_path, "a") as file:
        for segment in self.segments:
          print(segment.text)
          text = "[ " + str(segment.start) + " -> " + str(segment.end) + " ]" + segment.text + "\n"
          file.write(text)
        file.write("*" + "\n")
    upload_file_to_s3(self.local_transcript_path, transcript_path)

  def extract_time(self, time):
    time = time.split(".")
    seconds = int(time[0])
    hour = seconds//3600
    min = seconds//60
    sec = seconds%60
    millisec = int(time[1][:3])
    return hour, min, sec, millisec

  def create_transcript_segments(self):
    transcript_segments = []

    with open(self.local_transcript_path, "r") as file:
        for line in file:
          if len(line) < 2:
            continue

          line_elements = line.split()

          start = line_elements[1]
          hour, min, sec, millisec = self.extract_time(start)
          start_time = get_unixtime(hour, min, sec, millisec)

          end = line_elements[3]
          hour, min, sec, millisec = self.extract_time(end)
          end_time = get_unixtime(hour, min, sec, millisec)

          # inconsistency in transcription timestamps
          if end_time <= start_time:   # [ 121.24 -> 121.9 ] Thanks, Sam (end time should be 121.90) - handle this in the logic
              continue

          transcript_segments.append(Transcription(start_time, end_time, TranscribedText(line_elements[5:])))  

        return transcript_segments