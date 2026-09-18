class StyleBot:
    def __init__(self, client, persona, model):
        self.client = client
        self.persona = persona
        self.model = model
        self.history = []

    def ask(self, text_to_rewrite):
        """Rewrite only the input text, do not include original user question."""
        system_prompt = f"You are {self.persona}. Rewrite the following text in your style:"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text_to_rewrite}
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            reply = response.choices[0].message.content
        except Exception as e:
            reply = f"⚠️ Error: {str(e)}"

        # Only store rewritten text
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def clear_history(self):
        self.history = []
