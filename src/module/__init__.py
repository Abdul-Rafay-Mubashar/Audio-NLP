import setting
from src.module.QuizGenration import QuizGenerator
from src.module.NotesGenration import NotesGenerator

quiz_gen = QuizGenerator(openai_api_key=setting.OPEN_AI_API)
notes_gen = NotesGenerator(openai_api_key=setting.OPEN_AI_API)
notes_gen_router = NotesGenerator(openai_api_key=setting.OPEN_AI_API)

