

# The RAG Answer Generator. It is trainind on the Data from FB3/FB11
# Its just imported from the UniModulChatbot Project
# It should be adjusted for the use in the ComAI Project, but then Training Data is needed.
# It has still implemented the option to use a local LLM (Lama), but here it is not supported
"""
class RAGAnswerGenerator(AnswerGenerator):
    #TODO save vector_type also to the path
    def __init__(self, path, api2use='chatai'):
        AnswerGenerator.__init__(self)
        self.vector_path = os.path.join(path, 'chroma_db')
        self.client = chromadb.PersistentClient(path=self.vector_path)
        self.api2use = api2use
        if api2use == 'openai':
            # Configure sentence transformer embeddings
            self.sentence_transformer_ef = OpenAIEmbeddingFunction(
                model_name="text-embedding-3-small"
            )
        elif api2use == 'chatai':
            self.sentence_transformer_ef = OpenAIEmbeddingFunction(
                api_base=os.environ.get("BASE_URL"),
                api_key=os.environ.get("CHATAI_API_KEY"),
                model_name="e5-mistral-7b-instruct"
            )
        # Create or get existing collection
        self.collection = self.client.get_or_create_collection(
            name="documents_collection",
            embedding_function=self.sentence_transformer_ef
        )

    def generate_response(self, prompt):
        #Generate a response using OpenAI with conversation history
        if self.api2use == 'openai':
            openai_client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # or gpt-3.5-turbo for lower cost
                messages=[
                    {"role": "system", "content": "Du bist ein Studienassitent"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,  # Lower temperature for more focused responses
                max_tokens=500
            )
        else: # chatai
            openai_client = OpenAI(
                base_url=os.environ.get("BASE_URL"),
                api_key=os.getenv("CHATAI_API_KEY")
            )
            response = openai_client.chat.completions.create(
                model="openai-gpt-oss-120b",  # or gpt-3.5-turbo for lower cost
                messages=[
                    {"role": "system", "content": "Du bist ein Studienassitent"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,  # Lower temperature for more focused responses
                max_tokens=700
            )

        print("Used ChatAI")

        return response.choices[0].message.content

    def get_context_with_sources(self, results):
        #Extract context and source information from search results
        # Combine document chunks into a single context
        context = "\n\n".join(results['documents'][0])

        # Format sources with metadata
        sources = [
            f"{meta['source']} (chunk {meta['chunk']})"
            for meta in results['metadatas'][0]
        ]

        return context, sources

    def get_context(self, query, n_chunks = 3):
        #Perform RAG query: retrieve relevant chunks and generate answer
        # Get relevant chunks
        results = self.collection.query(
            query_texts=[query],
            n_results=n_chunks
        )
        context, sources = self.get_context_with_sources(results)
        return context, sources
    def get_answer(self, query, sources=[]):
        # Generate response
        response = self.generate_response(query)
        for source in sources:
            response += f'\n📁- {source}'
        return response

# Rule based Answer Generator is yet to be implemented
# Few open Question:
# - Use of an LLM with rules or not?
# - What rules are interessting?
#  
class RuleBasedLLMAnswerGenerator(AnswerGenerator):
    def __init__(self):
        AnswerGenerator.__init__(self, None)

    def get_answer(self, question, context):
        return "TODO IMPLEMENT"

# The variated LLM answer Generator.
# !!! HAVE TO CHECK IF THIS VERSION IS STILL IN USE OR CAN BE REPLACED!!!
class VariatedLLMAnswerGenerator(AnswerGenerator):
    def __init__(self, llm_type=None):
        self.api_key = os.environ.get("CHATAI_API_KEY")
        base_url = os.environ.get("BASE_URL")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=base_url
        )
        if llm_type in ['qwen-3-235b-a22b-thinking-2507']:
            self.model_name = llm_type
        else:
            self.model_name = 'qwen-3-235b-a22b-thinking-2507'

    def get_response(self, prompt, stream=False):
        print(prompt)
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": os.environ.get("MAIN_PROMPT")}, #The SystemPromt is from the .env file
                {"role": "user", "content": prompt}],
            max_tokens=2048,
            stop=None,
            temperature=0.6,
            top_p=0.95,
            stream=stream
        )
        return response

    def get_embedding(self, sentence):
        pass
        """