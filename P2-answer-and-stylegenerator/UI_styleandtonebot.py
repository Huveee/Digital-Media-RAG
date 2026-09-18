import gradio as gr
from openai import OpenAI
import os
import json
from dotenv import load_dotenv, find_dotenv
from flexible_style_detection import detect_style_and_tone

# Load .env
load_dotenv(find_dotenv())

# API configuration
api_key = os.environ.get("CHATAI_API_KEY")
base_url = os.environ.get("BASE_URL")
models = os.environ.get("MODELS").split(",")
models = [m.strip() for m in models if m.strip()]

# Start OpenAI client
client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

def answer_in_style(user_message: str, history: list) -> str:
    """Answer user in the detected style & tone of their input, with conversation memory."""
    # 1. Detect style & tone of the latest message
    result = detect_style_and_tone(user_message)
    info = result.get(user_message, {"style": "Unknown", "tone": "Unknown"})
    style, tone = info["style"], info["tone"]

    # 2. Convert Gradio history into OpenAI message format
    messages = []
    for msg in history or []:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Add instruction about style and tone for this response
    messages.append({
        "role": "system",
        "content": f"You are a helpful assistant. Always be factually correct. "
                   f"Now answer in this style and tone:\n- Style: {style}\n- Tone: {tone}"
    })

    # Add the latest user message
    messages.append({"role": "user", "content": user_message})

    # 3. Ask the model
    response = client.chat.completions.create(
        model=models[2],
        messages=messages,
        temperature=0.3
    )

    replytone = response.choices[0].message.content.strip()
    return replytone, info

# Chatbot logic
def chat(user_message, history):
    reply, info = answer_in_style(user_message, history)

    # Format response with style & tone info
    formatted_reply = f"""{reply}

---
🎭 **Style:** {info['style']}  
🎵 **Tone:** {info['tone']}"""

    history = history or []
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": formatted_reply})

    return "", history

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("## ✨ Style & Tone Detection Bot with Memory")

    chatbot = gr.Chatbot(type="messages")
    msg = gr.Textbox(placeholder="Ask me something...")
    clear = gr.Button("Clear Chat")

    # Example prompts
    gr.Markdown("### 📝 Example Prompts (click to insert):")
    with gr.Row():
        ex1 = gr.Button("Sprich, edler Freund, welches Geschöpf auf Gottes weiter Erde vermag am geschwindesten dahinzueilen unter dem Himmelszelt?")
        ex2 = gr.Button("Ey, wer droppt die krassesten Moves am Himmel, welcher Vogel fliegt höher als jeder Beat?")
        ex3 = gr.Button("Ey, welche App gönnt man sich am meisten, wenn man nur noch chillen will?")
        ex4 = gr.Button("Würden Sie so freundlich sein, mir mitzuteilen, welches Buch in der heutigen Literaturwelt als besonders einflussreich und lesenswert gilt?")

    # Clicking example fills textbox
    ex1.click(lambda x="Sprich, edler Freund, welches Geschöpf auf Gottes weiter Erde vermag am geschwindesten dahinzueilen unter dem Himmelszelt?": x, None, msg)
    ex2.click(lambda x="Ey, wer droppt die krassesten Moves am Himmel, welcher Vogel fliegt höher als jeder Beat?": x, None, msg)
    ex3.click(lambda x="Ey, welche App gönnt man sich am meisten, wenn man nur noch chillen will?": x, None, msg)
    ex4.click(lambda x="Würden Sie so freundlich sein, mir mitzuteilen, welches Buch in der heutigen Literaturwelt als besonders einflussreich und lesenswert gilt?": x, None, msg)

    msg.submit(chat, [msg, chatbot], [msg, chatbot])
    clear.click(lambda: ("", []), None, [msg, chatbot], queue=False)

demo.launch()
