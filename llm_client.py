from openai import OpenAI
from typing import Optional, Generator


class LLMClient:
    def __init__(self, name: str, base_url: str, api_key: str, model: str):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def chat(self, messages: list, system_prompt: Optional[str] = None) -> str:
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content

    def chat_stream(self, messages: list, system_prompt: Optional[str] = None) -> Generator[str, None, str]:
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        full_response = ""
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                delta = chunk.choices[0].delta.content
                full_response += delta
                yield full_response, delta
        return full_response

    def __repr__(self):
        return f"LLMClient({self.name}, {self.model})"
