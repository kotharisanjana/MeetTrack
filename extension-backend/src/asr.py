from common.utils import get_unixtime

from flask import current_app

class TranscribedText:
  def __init__(self, text):
    self.text = text
    self.init_obj = current_app.config["init_obj"]

class Transcription:
  def __init__(self, start_time, end_time, text):
    self.start_time = start_time
    self.end_time = end_time
    self.text = text 

class ASR:
  def __init__(self, audio_file_path):
    self.audio_file_path = audio_file_path

  def transcribe(self):
    self.segments, _ = self.init_obj.asr_model.transcribe(audio=self.audio_file_path, word_timestamps=True)

  def extract_time(self, time):
    time_str = str(time)
    time_str = time_str.split(".")
    seconds = int(time_str[0])
    hour = seconds//3600
    min = seconds//60
    sec = seconds%60
    millisec = int(time_str[1][:3])
    return hour, min, sec, millisec

  def transcription_segments(self):
    self.transcript_segments = []

    for segment in self.segments:
        start = segment.start
        hour, min, sec, millisec = self.extract_time(start)
        start_time = get_unixtime(hour, min, sec, millisec)

        end = segment.end
        hour, min, sec, millisec = self.extract_time(end)
        end_time = get_unixtime(hour, min, sec, millisec)

        # inconsistency in transcription timestamps
        if end_time.unixtime <= start_time.unixtime:   # [ 121.24 -> 121.9 ] Thanks, Sam (end time should be 121.90) - handle this in the logic
            continue

        self.transcript_segments.append(Transcription(start_time, end_time, TranscribedText(segment.text)))  

  def asr_pipeline(self):
    self.transcribe()
    self.transcription_segments()