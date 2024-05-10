from __init__ import llm_chat, logger
from src.guardrails.textual_gr import TextualGR

from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter
import re

class TextualComponent:
    def get_meeting_transcript(self, local_transcript_file):
        with open(local_transcript_file, "r") as file:
            self.transcript = file.read()    

    def process_transcript(self):
        chunk_size = 3000
        chunk_overlap = 200

        # Split the source text
        text_splitter = CharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        transcript_chunks = text_splitter.split_text(self.transcript)

        # Create Document objects for the chunks
        self.docs = [Document(page_content=t) for t in transcript_chunks[:]]

    def generate_textual_component(self):
        # chain of density prompting for generating meeting notes        
        prompt_template = """
            Act as a professional technical meeting minutes writer. 
            Generate a meeting summary in 50-100 words that provides a concise overview of the meeting and enclose it in <summary></summary> tags.
            Tone: formal
            Format: Technical meeting summary
            Length:  200 ~ 300
            After the summary, add the following sections and use bullet points if needed:
            Tasks:
            - highlight the key discussions
            - highlight action items with speaker names
            - highlight any other important details under appropriate headings
            {text}
            CONCISE MEETING NOTES IN ENGLISH:
            """

        PROMPT = PromptTemplate(template=prompt_template, input_variables=["text"])

        refine_template = (
        """
        We have provided existing meeting notes: {existing_answer}
        We now have the opportunity to refine the existing meeting notes (only if needed) with some more context below.
        ------------
        {text}
        ------------

        Given the new context, perform the following tasks:
        - Refine the summary that is enclosed in <summary></summary> tags and keep it in between the tags.
        - Ensure all sections and bullet points after the summary are maintained as is in the existing meeting notes, while excluding the meeting transcript sections.
        - Remove hallucinations and adhere to the actual meeting content.

        If the context isn't useful, return the original meeting notes as is.
        """
    )

        refine_prompt = PromptTemplate(
            input_variables=["existing_answer", "text"],
            template=refine_template,
        )

        try:
            chain = load_summarize_chain(
                llm_chat,
                chain_type="refine",
                return_intermediate_steps=True,
                question_prompt=PROMPT,
                refine_prompt=refine_prompt,
            )
            resp = chain({"input_documents": self.docs}, return_only_outputs=True)
            textual_component = resp["output_text"]

            logger.info("Textual component generated.")
        except Exception as e:
            logger.error(f"Error in generating textual component: {e}")
            textual_component = None

        return textual_component

    def textual_component_pipeline(self, local_transcript_path):
        self.get_meeting_transcript(local_transcript_path)
        self.process_transcript()

        textual_gr_obj = TextualGR(local_transcript_path)
        textual_gr_obj.setup_guard()

        max_tries = 3

        # call guardrails to ensure the correctness of the textual component
        while max_tries > 0:
            text = self.generate_textual_component()
            outcome = textual_gr_obj.validate(text)

            if outcome:
                if outcome.reask is None:
                    logger.info("Textual component creation completed and validated.")
                    return text
            
            max_tries -= 1

        logger.error("Textual component creation failed.")
        return "Caution: Meeting notes could not be validated: \n\n" + text
    
    def extract_summary_from_textual_component(self, textual_component):
        # Extract meeting summary based on <summary></summary> tags.
        pattern = r'<summary>(.*?)</summary>'
        match = re.search(pattern, textual_component, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        else:
            return None