import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# The LLM Answer Generator
class LLMRequester:
    def __init__(self, model_name: str):
        super().__init__() 
        self.api_key = os.environ.get("CHATAI_API_KEY")
        base_url = os.environ.get("BASE_URL") 
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)
        self.model_name = model_name
        

    def get_response(self, prompt, language="de", stream=False, max_tokens=2048, temperature=0.2, stop=None, image=None):
        system_prompt = (
            "Du bist ComAI, ein KI-Chatbot des ComAI-Projekts an der Universität Bremen. "
            "Das Projekt erforscht die Gestaltung und Implementierung von Konversations-KI-Schnittstellen als Dimension ihrer sozio-materiellen Konstitution. "
            "Als KI-Sprachmodell basieren deine Antworten auf Trainingsdaten, die möglicherweise unvollständig oder voreingenommen sind. "
            "Die Korrektheit deiner Ausgaben wird nicht während der Generierung überprüft. "
            "Weise Nutzer bei unsicheren oder kritischen Informationen darauf hin, Quellen eigenständig zu überprüfen und deren Qualität und Verlässlichkeit kritisch zu bewerten."
            if language == "de"
            else
            "You are ComAI, an AI chatbot of the ComAI project at the University of Bremen. "
            "The project researches the design and implementation of conversational AI interfaces as a dimension of their sociomaterial constitution. "
            "As a language model, your responses are based on training data that may be incomplete or biased, "
            "and the truthfulness of your output is not validated during generation. "
            "When information is uncertain or critical, encourage users to verify sources independently and critically evaluate the quality and reliability of the data."
        )

        print("=== get_response called ===")
        print("Prompt:", prompt)
        print("Model name:", self.model_name)

        if image:
            user_content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image}"}}
            ]
        else:
            user_content = prompt

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_content}
                     ],
            max_tokens=2048,
            temperature=0.2,
            top_p=0.95,
        )

        return response.choices[0].message.content

    def get_response_stream(self, prompt, language="de", image=None):
        """Yields content tokens as they arrive from the LLM."""
        system_prompt = (
            "Du bist ComAI, ein KI-Chatbot des ComAI-Projekts an der Universität Bremen. "
            "Das Projekt erforscht die Gestaltung und Implementierung von Konversations-KI-Schnittstellen als Dimension ihrer sozio-materiellen Konstitution. "
            "Als KI-Sprachmodell basieren deine Antworten auf Trainingsdaten, die möglicherweise unvollständig oder voreingenommen sind. "
            "Die Korrektheit deiner Ausgaben wird nicht während der Generierung überprüft. "
            "Weise Nutzer bei unsicheren oder kritischen Informationen darauf hin, Quellen eigenständig zu überprüfen und deren Qualität und Verlässlichkeit kritisch zu bewerten."
            if language == "de"
            else
            "You are ComAI, an AI chatbot of the ComAI project at the University of Bremen. "
            "The project researches the design and implementation of conversational AI interfaces as a dimension of their sociomaterial constitution. "
            "As a language model, your responses are based on training data that may be incomplete or biased, "
            "and the truthfulness of your output is not validated during generation. "
            "When information is uncertain or critical, encourage users to verify sources independently and critically evaluate the quality and reliability of the data."
        )

        if image:
            user_content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image}"}}
            ]
        else:
            user_content = prompt

        stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_content}],
            max_tokens=2048,
            temperature=0.2,
            top_p=0.95,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    def get_embedding(self, sentence):
        pass

class AnswerGenerator:
    def __init__(self):
        self.general_prompt = "A GENERAL ANSWER GENERATOR"
    def get_answer(self, question, context):
        return "Ich bin nur ein genereller Antwortgeber"


class LLMAnswerGenerator(AnswerGenerator):
    def __init__(self):
        AnswerGenerator.__init__(self)
        self.llm = LLMRequester()

    def get_answer(self, prompt):
        response_json = self.llm.get_response(prompt)
        return response_json.choices[0].message.content

