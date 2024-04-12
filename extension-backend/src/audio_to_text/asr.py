from common.utils import get_unixtime
from __init__ import asr_model
from common.aws_utilities import upload_file_to_s3

class TranscribedText:
  def __init__(self, text):
    self.text = text

class Transcription:
  # transcript segment object class
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
    # append transcript segment to local file and upload to S3 bucket
    with open(self.local_transcript_path, "a") as file:
        for segment in self.segments:
          text = "[ " + str(segment.start) + " -> " + str(segment.end) + " ]" + segment.text + "\n"
          file.write(text)

        # * marks end of one segment
        file.write("*" + "\n")

    upload_file_to_s3(self.local_transcript_path, transcript_path)


class TranscriptSegments():
  def extract_time(self, time):
    time = time.split(".")
    seconds = int(time[0])
    hour = seconds//3600
    min = seconds//60
    sec = seconds%60
    millisec = int(time[1][:3])
    return hour, min, sec, millisec

  def transcript_segments_pipeline(self, transcript_fp_start, local_transcript_path):
    transcript_segments = []

    with open(local_transcript_path, "r") as file:
        # read segment individually to process
        for _ in range(transcript_fp_start):
          file.readline()

        for line in file:
          # return on end of segment
          if len(line) < 3:
            transcript_fp_start += 1
            return transcript_segments, transcript_fp_start
          
          line_elements = line.split()

          start = line_elements[1]
          hour, min, sec, millisec = self.extract_time(start)
          start_time = get_unixtime(hour, min, sec, millisec)

          end = line_elements[3]
          hour, min, sec, millisec = self.extract_time(end)
          end_time = get_unixtime(hour, min, sec, millisec)

          # inconsistency in transcription timestamps
          if end_time <= start_time:
              continue
          
          text = " ".join(line_elements[5:])

          # append to list of transcript segments
          transcript_segments.append(Transcription(start_time, end_time, TranscribedText(text)))  

          transcript_fp_start += 1