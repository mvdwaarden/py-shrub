import base64

from ollama import chat, Client
from openai import OpenAI
from typing import List


class ChatClient:    
    def __init__(self, url: str, temperature: float = 0.1, key: str = None):
        self.url = url
        self.temperature: float = temperature
        self.key = key 
    
    def chat(self, model_name: str, prompt_instructions: str, image_path: List[str] = None) -> str:
        # Implement chat functionality here
        pass
    
    


class OllamaChat(ChatClient):
    def __init__(self, url:str, temperature: float = 0.1, key: str = None):       
        super().__init__(url, temperature, key)
        self.client = None
    
    def chat(self, model_name: str, prompt_instructions: str, images: List[str] = None) -> str:
        def _read_image(image_path: str) -> str:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        
        try:
            if not self.client:
                self.client = Client(host=self.url)
            client = self.client
            response = client.chat(
                model=model_name,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt_instructions,
                        'images': [f"{_read_image(images[0])}"]
                    }
                ],
                options={
                    'temperature': self.temperature  # Keep temperature low for deterministic, accurate OCR text
                }
            )   
            result = response.message.content if response else "No response received from the model."
        except Exception as e:
            result = f"Error during chat: {e}"
     
        return result

class OpenAiChat(ChatClient):
    def __init__(self, url:str, temperature: float = 0.1, key: str = None):       
        super().__init__(url, temperature, key)
        self.client = None
    
    def chat(self, model_name: str, prompt_instructions: str, images: List[str] = None) -> str:        
        def _read_image_file_as_base64(image_path: str) -> str:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        try:
            if not self.client:
                self.client = OpenAI(
                    base_url=self.url,
                    api_key=self.key if self.key else "no-key-required-for-local"
                )
            client = self.client
            messages = [
                    {
                        'role': 'user',
                        'content': [
                            {
                                "type": "text", 
                                "text": prompt_instructions,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{_read_image_file_as_base64(images[0])}" 
                                }
                            }
                        ]
                    }
            ]
            response = client.chat.completions.create(
                model=model_name,
                messages=messages
            )  
            result = response.choices[0].message.content if response.choices else "No response received from the model."
        except Exception as e:
            result = f"Error during chat: {e}"
     
        return result




