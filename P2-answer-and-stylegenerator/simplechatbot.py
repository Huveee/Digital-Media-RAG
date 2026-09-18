from openai import OpenAI

class ChatBot:
    def __init__(self, client, persona, model):
        self.client = client
        self.persona = persona
        self.model = model
        self.history = []

    def ask(self, user_message):
        system_prompt = f"You are {self.persona}."

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.history)
        messages.append({"role": "user", "content": user_message})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            reply = response.choices[0].message.content
        except Exception as e:
            reply = f"⚠️ Error: {str(e)}"

        # Verlauf speichern
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": reply})

        return reply

    def clear_history(self):
        self.history = []
