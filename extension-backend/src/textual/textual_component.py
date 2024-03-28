from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from common.aws_utilities import download_textfile_from_s3
from database.relational_db import fetch_curr_transcript_path
from __init__ import llm_chat

class TextualComponent:
    def get_meeting_transcript(self, meeting_id):
        transcript_path = fetch_curr_transcript_path(meeting_id)
        self.transcript_str = download_textfile_from_s3(transcript_path)

    def create_document_from_transcript(self):
        chunk_size = 3000
        chunk_overlap = 200
        # Split the source text
        text_splitter = CharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        transcript_chunks = text_splitter.split_text(self.transcript_str)
        # Create Document objects for the chunks
        self.docs = [Document(page_content=t) for t in transcript_chunks[:]]

    def generate_textual_component(self):
        target_len = 500
        
        prompt_template = """
            Act as a professional technical meeting minutes writer.
            Tone: formal
            Format: Technical meeting summary
            Length:  200 ~ 300
            Tasks:
            - highlight action items and owners
            - highlight the agreements
            - Use bullet points if needed
            {text}
            CONCISE SUMMARY IN ENGLISH:
        """

        PROMPT = PromptTemplate(template=prompt_template, input_variables=["text"])

        refine_template = (
            "Your job is to produce a final summary\n"
            "We have provided an existing summary up to a certain point: {existing_answer}\n"
            "We have the opportunity to refine the existing summary"
            "(only if needed) with some more context below.\n"
            "------------\n"
            "{text}\n"
            "------------\n"
            f"Given the new context, refine the original summary in English within {target_len} words: following the format"
            "Participants: <participants>"
            "Discussed: <Discussed-items>"
            "Follow-up actions: <a-list-of-follow-up-actions-with-owner-names>"
            "If the context isn't useful, return the original summary. Highlight agreements and follow-up actions and owners."
        )

        refine_prompt = PromptTemplate(
            input_variables=["existing_answer", "text"],
            template=refine_template,
        )

        chain = load_summarize_chain(
            llm_chat,
            chain_type="refine",
            return_intermediate_steps=True,
            question_prompt=PROMPT,
            refine_prompt=refine_prompt,
        )
        resp = chain({"input_documents": self.docs}, return_only_outputs=True)
        textual_component = resp["output_text"]

        return textual_component


    def textual_component_pipeline(self, meeting_id):
        self.get_meeting_transcript(meeting_id)
        self.create_document_from_transcript()
        return self.generate_textual_component()