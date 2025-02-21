from openai import OpenAI
from config import DEEPSEEK_API_KEY, OPENAI_API_KEY
from enum import Enum

class AIModel(Enum):
    OPENAI = "openai"
    DEEPSEEK = "deepseek"

class AIService:
    def __init__(self, model_type: AIModel):
        self.model_type = model_type
        if model_type == AIModel.DEEPSEEK:
            self.client = OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com"
            )
        else:  # OpenAI
            self.client = OpenAI(api_key=OPENAI_API_KEY)

    def create_completion(self, messages):
        try:
            if self.model_type == AIModel.DEEPSEEK:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    stream=False
                )
            else:  # OpenAI
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=messages
                )
            return True, response.choices[0].message.content
        except Exception as e:
            return False, str(e)

def test_ai_connection(model_type: AIModel):
    ai_service = AIService(model_type)
    return ai_service.create_completion([
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Test connection"}
    ])