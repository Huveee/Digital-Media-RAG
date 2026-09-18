import os
from openai import OpenAI
from dotenv import load_dotenv
from Chatbots.AnswerGenerator import AnswerGenerator
import json


load_dotenv()

with open(os.getenv("VARLLM_STYLES"), "r", encoding="utf-8") as f:
    var_styles = json.load(f)


def get_varllm_style_prompt(style: str, language: str) -> str:
    style = style.lower()
    language = language.lower()

    try:
        return var_styles[style][language]
    except KeyError:
        # Fallback
        return (
            "You are a helpful assistant."
            if language == "en"
            else "Du bist ein hilfsbereiter Assistent."
        )

#This is the currently used Version of the VariantLM
class VariatedLLMAnswerGenerator(AnswerGenerator):
    def __init__(self, model_name: str):
        super().__init__() 
        self.api_key = os.environ.get("CHATAI_API_KEY")
        base_url = os.environ.get("BASE_URL") 
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)
        self.model_name = model_name

    def get_response(self, prompt: str, language="de", variationPrompt="", image=None):
        style_prompt = get_varllm_style_prompt(variationPrompt, language)

        if image:
            user_content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image}"}}
            ]
        else:
            user_content = prompt

        # Anfrage an OpenAI senden
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "system", "content": style_prompt},
                      {"role": "user", "content": user_content}
                     ],
            max_tokens=2048,
            temperature=0.4,
            top_p=0.95,
        )

        # Antwort extrahieren
        answer = response.choices[0].message.content


        return answer

    def get_response_stream(self, prompt: str, language="de", variationPrompt="", image=None):
        """Yields content tokens as they arrive from the LLM."""
        style_prompt = get_varllm_style_prompt(variationPrompt, language)

        if image:
            user_content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image}"}}
            ]
        else:
            user_content = prompt

        stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "system", "content": style_prompt},
                      {"role": "user", "content": user_content}],
            max_tokens=2048,
            temperature=0.4,
            top_p=0.95,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    def get_embedding(self, sentence):
        pass
