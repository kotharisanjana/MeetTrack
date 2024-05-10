from database.vector_db import get_actual_speaker

def combine_asr_diarization(speaker_segments, transcript_segments):

    tl = len(transcript_segments)
    dl = len(speaker_segments)

    if tl == 0 or dl == 0:
        return ""

    segment_num = 1

    # get actual speaker based on voice embeddings
    actual_speaker = get_actual_speaker(int(speaker_segments[0].speaker.speaker_id))
    overall_text = actual_speaker + ":" + transcript_segments[0].text.text + "\n\n"

    # create final output by assigning actual speakers to dialogues
    for segment in speaker_segments:
        detime = segment.end_time
        speaker_id = segment.speaker.speaker_id

        actual_speaker = get_actual_speaker(int(speaker_id))

        if segment_num!=1:
            overall_text = overall_text + "\n\n" + actual_speaker + ": "

        while segment_num < tl:
            tstime = transcript_segments[segment_num].start_time

            # exact overlap window cannot be found because the diarization and transcription time segments are not consistent and words might overflow into new window
            if tstime <= detime:
                overall_text = overall_text + transcript_segments[segment_num].text.text
            else:
                break

            segment_num += 1

    return overall_text