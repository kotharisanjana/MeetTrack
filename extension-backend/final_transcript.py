from setup import vector_db_obj

def combine_asr_diarization(speaker_segments, transcript_segments):
    l = len(transcript_segments)

    segment_num = 1

    actual_speaker = vector_db_obj.get_actual_speaker(str(int(speaker_segments[0].speaker.speaker_id)))
    overall_text = "Speaker " + actual_speaker + ":" + transcript_segments[0].text.text

    for segment in speaker_segments:
        # dstime = segment.start_time.unixtime
        detime = segment.end_time.unixtime
        speaker_id = segment.speaker.speaker_id

        actual_speaker = vector_db_obj.get_actual_speaker(str(int(speaker_id)))

        if segment_num!=1:
            overall_text = overall_text + "\n" + "Speaker " + actual_speaker + ":"

        while segment_num<l:
            tstime = transcript_segments[segment_num].start_time.unixtime
            # tetime = transcript_segments[segment_num].end_time.unixtime

            # exact overlap window cannot be found because the diarization and transcription time segments are not consistent and words might overflow into new window
            if tstime <= detime:
                overall_text = overall_text + transcript_segments[segment_num].text.text
            else:
                break

            segment_num += 1

    return overall_text