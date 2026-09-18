from Chatbots.AnswerGenerator import LLMAnswerGenerator, RAGAnswerGenerator
import os

# The Modulchatbot for FB11
class DomainBot:
    def __init__(self, name, domain=None,  lang='de'):
        self.name = None
        self.domain = domain
        self.lang = lang
        self.description = ''
        self.welcome_message = ''
        #self.answer_generator = AnswerGenerator()

    def get_prompt(self):
        return f"Du bist ein Assistent der sich insbesondere in der Domäne {self.domain} auskennt, " \
               f"dein Name ist {self.name}"


class OpenDomainBot(DomainBot):
    def __init__(self, name = None):
        DomainBot.__init__(self, 'Open Domain', domain='das Wissen des Internets')


class ModulchatBotFB11(DomainBot):
    def __init__(self):
        DomainBot.__init__(self,
                           'Modulchatbot des Fachbereichs 11 an der Uni Bremen',
                           'Informationen zum Studium der Gesundheitswissenschaften')
        #self.answer_generator = LLMAnswerGenerator()
        self.answer_generator = RAGAnswerGenerator(path=os.path.join('.', 'data', 'fb11_data'))
        self.history = []

    def get_prompt(self, question, context=None):
        """
        prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>" \
               f"\n\nSie sind ein hilfreicher Assistent, " \
               f"der Fragen auf der Grundlage des bereitgestellten Kontextes beantwortet." \
               f"\n<|eot_id|><|start_header_id|>user<|end_header_id|>" \
               f"\n\nKontextes: {context_text} \n\n " \
               f"Beantworten Sie die Frage auf der Grundlage des obigen Kontextes: {user_prompt}" \
               f"\n<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
        """
        prompt = f"Du bist der Studienberater der Universität Bremen im Fachbereich 11, Gesundheitswissenschaften. " \
                 f"Du kennst dich zu der Prüfungsordnung aus und zu den verschiedenen Modulen die im Studium belegt " \
                 f"werden müssen. Es ist wichtig, dass du so Faktenbasiert wie möglich antwortest und immer freundlich" \
                 f"bleibst. Die Nutzer*innen haben folgende Frage gestellt {question}"
        if context is not None:
            prompt += f"Beantworten Sie die Frage auf der Grundlage des Kontextes: {context}"
        return prompt

    def get_response(self, question):
        #return self.answer_generator.get_answer(self.get_promt(question))
        context, sources = self.answer_generator.get_context(question)
        prompt = self.get_prompt(question, context)
        answer = self.answer_generator.get_answer(prompt, sources)
        return answer