from pydantic import BaseModel

class RuntimeConfig(BaseModel):
    active_bot:         str = "llm"        # "llm", "varllm"
    variation_enabled:  bool = False # True/False
    variation_type:     str = "metaphor"  # "similarword","hedging","metaphor","style"
    varllm_style:       str = "board"       # "joyful","detailed","casual","professional","board"
    llm_model_name:     str = "meta-llama-3.1-8b-instruct" # change to your preferred model from list below
    varllm_model_name:  str = "meta-llama-3.1-8b-instruct" # ""
    language:           str = "de" # or "en"

# Possible models:
# deepseek-r1,meta-llama-3.1-8b-instruct,meta-llama-3.1-8b-rag,llama-3.1-sauerkrautlm-70b-instruct,llama-3.3-70b-instruct
# gemma-3-27b-it,mistral-large-instruct,qwen3-235b-a22b,qwen3-32b,openai-gpt-oss-120b

