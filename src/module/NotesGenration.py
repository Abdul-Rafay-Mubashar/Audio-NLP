import subprocess
import math
import os, shutil
import win32com.client
import traceback


from docx import Document
from openai import OpenAI
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0 


class NotesGenerator:
    def __init__(self, openai_api_key):
        self.client = OpenAI(api_key=openai_api_key)
        self.path = rf"C:\Users\Hp\Desktop\FYP\recording"

    def run_command(self, cmd):
        """Run a shell command and return stdout as string."""
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Command {' '.join(cmd)} failed with error: {result.stderr.strip()}")
        return result.stdout.strip()

    def get_file_duration(self, file_path):
        """Return duration in seconds."""
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        output = self.run_command(cmd)
        if output == "N/A" or not output:
            raise RuntimeError("Could not get duration")
        return float(output)

    def get_audio_bitrate(self, file_path):
        """Return audio bitrate in bits per second."""
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=bit_rate",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        bitrate = self.run_command(cmd)
        if bitrate == "N/A" or not bitrate:
            # fallback to format bitrate
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=bit_rate",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ]
            bitrate = self.run_command(cmd)
        if bitrate == "N/A" or not bitrate:
            raise RuntimeError("Could not get bitrate")
        return int(bitrate)

    def split_file_by_size(self, file_path, target_chunk_size_mb=25, output_prefix="chunk_"):
        """
        Split file into chunks approximately target_chunk_size_mb each (in MB).
        Splits by duration estimated from bitrate.
        """
        duration = self.get_file_duration(file_path)
        bitrate = self.get_audio_bitrate(file_path)  # in bits per second

        # Calculate chunk duration so that chunk size ~= target_chunk_size_mb MB
        # size_in_bits = bitrate * duration
        # chunk_duration = (target_chunk_size_mb * 8 * 1024 * 1024) / bitrate
        target_chunk_size_bits = target_chunk_size_mb * 8 * 1024 * 1024
        chunk_duration = target_chunk_size_bits / bitrate

        num_chunks = math.ceil(duration / chunk_duration)
        print(f"num-chunks : {num_chunks}")

        print(f"File duration: {duration:.2f} sec")
        print(f"Audio bitrate: {bitrate} bps")
        print(f"Chunk duration for ~{target_chunk_size_mb} MB chunks: {chunk_duration:.2f} sec")
        print(f"Number of chunks: {num_chunks}")

        # Create output directory for chunks
        output_dir = os.path.join(self.path, "chunks")
        os.makedirs(output_dir, exist_ok=True)

        for i in range(num_chunks):
            start = i * chunk_duration
            output_file = os.path.join(output_dir, f"{output_prefix}{i+1}.webm")

            cmd = [
                "ffmpeg", "-y",
                "-i", file_path,
                "-ss", str(start),
                "-t", str(chunk_duration),
                "-c", "copy",
                output_file
            ]
            print(f"Creating chunk {i+1}: {output_file}")
            subprocess.run(cmd, check=True)
        return num_chunks

    def remove_silence(self, input_file, output_file):
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-af', 'silenceremove=stop_periods=-1:stop_duration=0.5:stop_threshold=-40dB',
            '-y',
            output_file
        ]
        subprocess.run(cmd, check=True)
        return output_file

    def fix_file(self, input_file, output_file):
        cmd = [
            "ffmpeg", "-y", "-i", input_file,
            "-c", "copy",
            output_file
        ]
        print(f"Fixing file: {input_file} -> {output_file}")
        subprocess.run(cmd, check=True)
        return output_file

    def count_chunk_files(self, folder_path, prefix="chunk"):
        try:
            return len([
                f for f in os.listdir(folder_path)
                if os.path.isfile(os.path.join(folder_path, f)) and f.startswith(prefix)
            ])
        except FileNotFoundError:
            print(f"Folder not found: {folder_path}")
            return 0

    def audio_translation_to_english(self, total: int):
        path = os.path.join(self.path, "chunks")
        text = ""
        print(total)
        for num in range(total):
            print(num)

            with open(f"{path}\chunk_{num+1}.webm", "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="json",
                    language='en'  # you can also use 'json' or 'srt'
                )
            text = text + transcript.text + " "
        return text
    
    def detect_language(self, text):
        try:
            lang = detect(text)
            return lang
        except Exception as e:
            print(f"Error detecting language: {e}")
            return None

    def audio_language_detection(self, filepath: str):

        with open(filepath, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="json",
                )
            text = transcript.text
        lang_code = self.detect_language(text)
        return lang_code    
    
    def delete_files(self, file_paths):
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                else:
                    print(f"File not found: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

    def empty_folder(self, folder_path):
        if not os.path.exists(folder_path):
            print(f"Folder does not exist: {folder_path}")
            return

        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)

            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.remove(item_path)
                    print(f"Deleted file: {item_path}")
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    print(f"Deleted folder: {item_path}")
            except Exception as e:
                print(f"Error deleting {item_path}: {e}")

    def extract_middle_chunk(self, input_path, output_path, chunk_duration=30):
        """
        Extract a middle chunk of audio/video from file.
        """
        print(input_path, output_path)
        duration = self.get_file_duration(input_path)
        if duration is None:
            print("Cannot get duration; skipping extraction.")
            return

        if duration < chunk_duration:
            print("File shorter than chunk duration; copying full file.")
            subprocess.run(['ffmpeg', '-y', '-i', input_path, '-c', 'copy', output_path])
            return output_path

        start_time = (duration / 2) - (chunk_duration / 2)
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(start_time),
            '-t', str(chunk_duration),
            '-i', input_path,
            '-c', 'copy',
            output_path
        ]
        print(f"Extracting {chunk_duration}s from middle starting at {start_time}s...")
        subprocess.run(cmd, check=True)
        print(f"Saved chunk to {output_path}")
        return output_path


    def audio_processor(self, input_file: str): 
        try:
            input_path = os.path.join(self.path, input_file)
            if os.path.exists(input_path):
                fixed_filename = f"fixed_{input_file}"
                fixed_file = self.fix_file(input_path, os.path.join(self.path, fixed_filename))
                silent_filename = f"silent_{input_file}"
                silence_file = self.remove_silence(fixed_file, os.path.join(self.path, silent_filename))
                middle_filename = f"middle_{input_file}"
                middle_file = self.extract_middle_chunk(silence_file, os.path.join(self.path, middle_filename))
                print(middle_file, middle_filename) 
                language = self.audio_language_detection(middle_file)
                print(f"Language Detected : {language}")
                print(f"Language De : {language}")

                self.split_file_by_size(silence_file, target_chunk_size_mb=20)
                chunks_num = self.count_chunk_files(folder_path=os.path.join(self.path, "chunks"))
                eng_text = self.audio_translation_to_english(chunks_num)
                print(f"english text: {eng_text}")
                self.delete_files([fixed_file,silence_file,input_path, middle_file])
                self.empty_folder(os.path.join(self.path, "chunks"))
                print(f"Chunk folder emptyed")

                return eng_text, language
            
        except Exception as e:
            print(f"NotesGenration -->audio_processor: Error in translation {str(e)}, {fixed_filename}, {middle_filename}, {silent_filename}")
            traceback.print_exc() 
            return None, None    



    def generate_notes(self, text: str) -> str:
        """Generates structured notes based on the text using OpenAI API."""
        response = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "user",
                    "content": (
                        "You are a notes generator. You are given a lecture transcription text. "
                        "Your task is to summarize and generate clear, structured notes in paragraghs with detail"
                        "Also give the example of topics disscus in text"
                        "Explain everything in detail"
                        "If it is not complete lecture just send back elabrating text"
                        f"Here is the text:\n\n{text}"
                    ),
                }
            ],
        )
        return response.choices[0].message.content.strip()
    

    def convert_docx_to_pdf(self, input_path, output_path):
        word = win32com.client.Dispatch("Word.Application")
        doc = word.Documents.Open(input_path)
        doc.SaveAs(output_path, FileFormat=17)  # 17 = wdFormatPDF
        doc.Close()
        word.Quit()
        print(f"✅ Converted to PDF: {output_path}")


    def save_text_to_word(self, text: str, docx_path: str):
        doc = Document()
        doc.add_paragraph(text)  # This automatically wraps long lines
        doc.save(docx_path)
        print(f"✅ Word document saved to: {docx_path}")

    
