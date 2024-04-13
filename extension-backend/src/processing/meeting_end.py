from src.textual.textual_component import TextualComponent
from src.visual.visual_component import VisualComponent
from src.output.final_doc import create_final_doc
from src.output.email import send_email
from common.utils import delete_files
from database.cache import delete_session
from __init__ import logger

def on_end_processing(session_data):
  meeting_id = session_data["meeting_id"]
  session_id = session_data["session_id"]

  # generate textual component
  textual_component_obj = TextualComponent()
  textual_component = textual_component_obj.textual_component_pipeline(session_data["local_transcript_path"])
  logger.info("Textual component creation completed.")

  # extract summary from textual component
  if textual_component:
    summary = textual_component_obj.extract_summary_from_textual_component(textual_component)
  else:
    summary = None

  # summary = """The meeting focused on the importance of vaccine mandates and the need to address staff concerns. The discussion highlighted the need for ongoing communication and consideration of alternative approaches. The potential risks of the virus spreading once borders open were also emphasized, leading to a cautious approach in decision-making."""
  # meeting_id = 362

  # image-context and get image links
  if summary:
    image_url_desc_pairs = VisualComponent(meeting_id).get_contextual_images_from_summary(summary)
  else:
    image_url_desc_pairs = {}

  logger.info("Visual component creation completed.")

  # merge into final output doc
  create_final_doc(session_data, textual_component, image_url_desc_pairs)
  logger.info("Final document creation completed.")

  # email meeting notes to recipient
  send_email(session_data)

  # cleanup on meeting end
  cleanup(session_id, meeting_id)


def cleanup(session_id, meeting_id):
  # delete files from local file system
  delete_files(meeting_id)

  # terminate session
  delete_session(session_id)