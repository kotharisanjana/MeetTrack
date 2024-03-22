from common.aws_utilities import get_s3_image_bytes, upload_file_to_s3
from docx import Document
from docx.shared import Inches
from io import BytesIO
from PIL import Image

def create_final_doc(textual_component, image_keys, output_path):
    doc = Document()
    doc.add_paragraph(textual_component)
    
    for key in image_keys:
        image_bytes = get_s3_image_bytes(key)

        if image_bytes:
            # Convert bytes to a PIL Image
            image = Image.open(BytesIO(image_bytes))

            # Calculate the image's width and height in inches for the document
            width, height = image.size
            aspect_ratio = height / width
            display_width = min(4.0, width / 72) 
            display_height = display_width * aspect_ratio
            
            # Add image to the document
            image_stream = BytesIO(image_bytes)
            doc.add_picture(image_stream, width=Inches(display_width), height=Inches(display_height))
            
    upload_file_to_s3(doc, output_path)