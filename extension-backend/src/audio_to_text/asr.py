from common.utils import get_unixtime
from __init__ import asr_model

class TranscribedText:
  def __init__(self, text):
    self.text = text

class Transcription:
  def __init__(self, start_time, end_time, text):
    self.start_time = start_time
    self.end_time = end_time
    self.text = text 

class ASR:
  def __init__(self, meeting_audio):
    self.meeting_audio = meeting_audio

  def transcribe(self):
    self.segments, _ = asr_model.transcribe(audio=self.meeting_audio, word_timestamps=True)

  def extract_time(self, time):
    time_str = str(time)
    time_str = time_str.split(".")
    seconds = int(time_str[0])
    hour = seconds//3600
    min = seconds//60
    sec = seconds%60
    millisec = int(time_str[1][:3])
    return hour, min, sec, millisec

  def merge_transcription_segments(self):
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
    self.merge_transcription_segments()