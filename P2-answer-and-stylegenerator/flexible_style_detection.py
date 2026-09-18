from openai import OpenAI
import os
from dotenv import load_dotenv, find_dotenv

# Load .env
load_dotenv(find_dotenv())

# API configuration
api_key = os.environ.get("CHATAI_API_KEY")
base_url = os.environ.get("BASE_URL")
models = os.environ.get("MODELS").split(",")
models = [m.strip() for m in models if m.strip()]

# Start OpenAI client
client = OpenAI(
    api_key = api_key,
    base_url = base_url
)

def detect_style_and_tone(texts):
    """
    Detects both the language style and tone of one or multiple text inputs using an LLM.
    The LLM generates descriptive style and tone in its own words.
    
    :param texts: str or list of str
    :return: dict with input -> {style: ..., tone: ...}
    """
    if isinstance(texts, str):
        texts = [texts]

    results = {}
    for t in texts:
        prompt = f"""
        Analyze the following text and describe both its language style and tone.
        - Style: Describe the writing style (e.g., formal, casual, academic, poetic, technical, persuasive).
        - Tone: Describe the tone or emotional quality (e.g., serious, humorous, optimistic, sarcastic, passionate).
        
        Text:
        \"\"\"{t}\"\"\"
        
        Return the response in JSON format:
        {{
            "style": "...",
            "tone": "..."
        }}
        """

        response = client.chat.completions.create(
            model="openai-gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        # Parse the response text into a dictionary
        try:
            import json
            style_tone = json.loads(response.choices[0].message.content.strip())
        except Exception:
            # fallback if JSON parsing fails
            style_tone = {"style": "Unknown", "tone": "Unknown"}

        results[t] = style_tone

    return results


if __name__ == "__main__":
    # Example usage
    samples = [
        "The results of this experiment demonstrate a significant correlation.",
        "Yo, what's up? Wanna grab some food later?",
        "Shall I compare thee to a summer’s day? Thou art more lovely and more temperate.",
        "Ladies and gentlemen, we gather here today to celebrate innovation and progress.",
        "I can't believe you actually did that! Totally unexpected."
    ]

    analysis = detect_style_and_tone(samples)
    for text, info in analysis.items():
        print(f"Text: {text}\nStyle: {info['style']}\nTone: {info['tone']}\n")