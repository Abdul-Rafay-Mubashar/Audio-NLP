import re
import spacy
import pdfplumber

from openai import OpenAI


class QuizGenerator:
    def __init__(self, openai_api_key):
        self.client = OpenAI(api_key=openai_api_key)
        self.nlp = spacy.load("en_core_web_sm")

    def extract_text_from_pdf(self, paths: list):
        """Extract text from PDF file."""
        text = ""
        print(paths)
        for path in paths:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
        print(f"Here Sucessfully {text}")
        return text

    def segment_text(self, text):
        """Splits text into sections using NLP-based sentence segmentation."""
        doc = self.nlp(text)
        sections = []
        current_section = []

        for sent in doc.sents:
            if sent.text.strip().endswith(":") or sent.text.strip().istitle():
                if current_section:
                    sections.append(" ".join(current_section))
                current_section = [sent.text]
            else:
                current_section.append(sent.text)

        if current_section:
            sections.append(" ".join(current_section))

        return sections

    def extract_code_and_queries(self, text):
        """Extracts code snippets and SQL queries separately, accounting for different formats."""
        code_block_pattern = re.compile(r"```(.*?)```", re.DOTALL)
        inline_code_pattern = re.compile(r"`(.*?)`")
        sql_pattern = re.compile(
            r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|REPLACE|TRUNCATE|MERGE)\b.*?;",
            re.DOTALL | re.IGNORECASE,
        )
        code_snippets = code_block_pattern.findall(
            text
        ) + inline_code_pattern.findall(text)
        sql_queries = sql_pattern.findall(text)
        return code_snippets, sql_queries

    def distribute_mcqs(self, num_sections, total_mcqs):
        base = total_mcqs // num_sections
        extra = total_mcqs % num_sections
        distribution = [base] * num_sections
        for i in range(extra):
            distribution[i] += 1
        print(distribution)
        return distribution

    def add_all_content(
        self, sql_queries, code, sections: list, mcqs_count: int
    ):
        """Combine code snipts and sql quries into section if any exisits"""
        sections.append(sql_queries)
        sections.append(code)
        print(f"Length of Section before cleaning {len(sections)}")
        sections[:] = [section for section in sections if section != "" and section != []]
        print(f"Length of Section after cleaning {len(sections)}")
        distribution = self.distribute_mcqs(len(sections), mcqs_count)
        return sections, distribution

    def generate_mcqs(self, sections, distribution: list):
        """Generates MCQs based on the segmented sections using OpenAI API."""
        mcqs = []
        distribution_no = 0
        for section in sections:
            if distribution[distribution_no] == 0:
                continue
            prompt = (
                f"You are an expert quiz generator. Generate {distribution[distribution_no]} multiple-choice questions based on the following content:\n\n"
                f"{section}\n\n"
                "Each question should have the following JSON format:\n"
                """[
                    {
                        "statement": "Question text here?",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "correct_answer": "Option A"
                    }
                ]\n\n"""
                "Please respond with only a valid JSON array of questions, no explanations or extra text."
            )
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": prompt, 
                    }
                ],
                temperature= 0.7

            )
            mcqs.append(response.choices[0].message.content)
            distribution_no = distribution_no + 1
            print(f"quiz content: {response.choices[0].message.content} from section {section}")
        return mcqs

    def genrate_quiz(self, paths: list, mcqs_count: int):
        """Prints the generated MCQs."""
        print(paths)
        pdf_text = self.extract_text_from_pdf(paths)
        code, sql_queries = self.extract_code_and_queries(pdf_text)
        text_content = self.segment_text(pdf_text)
        sections, distribution = self.add_all_content(
            sql_queries, code, text_content, mcqs_count
        )
        print(sections)
        mcqs = self.generate_mcqs(sections, distribution)
        return mcqs

