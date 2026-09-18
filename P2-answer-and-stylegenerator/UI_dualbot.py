import os
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
import gradio as gr
from adaptive_style import AdaptiveResponder

# Load .env
load_dotenv(find_dotenv())

# API configuration
api_key = os.environ.get("CHATAI_API_KEY")
base_url = os.environ.get("BASE_URL")
models = os.environ.get("MODELS").split(",")
models = [m.strip() for m in models if m.strip()]

# Start OpenAI client
client = OpenAI(api_key=api_key, base_url=base_url)

# Style engines
style_engine1 = AdaptiveResponder()
style_engine2 = AdaptiveResponder()

# ---- Core Chat Function ----
def chat_with_bot(user_message, history, style_engine, *, model, persona="Helpful assistant"):
    style_engine.observe_question(user_message)
    style = style_engine.profile

    system_prompt = f"You are {persona}."
    if style.tone == "casual":
        system_prompt += " Answer in a casual, friendly tone."
    elif style.tone == "formal":
        system_prompt += " Answer in a formal, professional tone."
    else:
        system_prompt += " Answer in a neutral, clear tone."
    if style.use_emojis:
        system_prompt += " Add emojis when appropriate."
    if style.use_exclaims:
        system_prompt += " You may use exclamation marks."
    if style.structure == "list":
        system_prompt += " Prefer structured lists."
    if style.wants_code:
        system_prompt += " Provide Python code snippets if helpful."

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    reply = response.choices[0].message.content
    return reply, style_engine.current_profile()


# ---- Gradio UI ----
with gr.Blocks() as demo:
    gr.Markdown("## 🤖 Bot 1 → Bot 2 Pipeline")

    with gr.Row():
        # Bot 1 input/output
        with gr.Column():
            gr.Markdown("### Bot 1: Friendly Assistant (User Input)")
            model1 = gr.Dropdown(models, value=models[0], label="Select Model for Bot 1")
            chatbot1 = gr.Chatbot(type="messages")
            msg1 = gr.Textbox(placeholder="Type your question here...")
            clear1 = gr.Button("Clear Bot 1")
            style_box1 = gr.JSON(label="Bot 1 Style")

        # Bot 2 output only
        with gr.Column():
            gr.Markdown("### Shakespearean Rewriter (Bot 1 Output)")
            model2 = gr.Dropdown(models, value=models[1] if len(models) > 1 else models[0],
                                 label="Select Model for Bot 2")
            chatbot2 = gr.Chatbot(type="messages")
            style_box2 = gr.JSON(label="Bot 2 Style")

    # ---- Function: User asks Bot 1, Bot 2 rewrites ----
    def ask_and_rewrite(user_message, history1, history2, model_choice1, model_choice2):
        # Bot 1 answers
        reply1, style1 = chat_with_bot(
            user_message,
            history1,
            style_engine1,
            model=model_choice1,
            persona="a friendly helpful assistant"
        )
        history1.append({"role": "user", "content": user_message})
        history1.append({"role": "assistant", "content": reply1})

        # Bot 2 rewrites Bot 1 answer
        rewrite_prompt = f"Rewrite the following answer in your style:\n\n{reply1}"
        reply2, style2 = chat_with_bot(
            rewrite_prompt,
            history2,
            style_engine2,
            model=model_choice2,
            persona="you are shakespeare"
        )
        history2.append({"role": "user", "content": rewrite_prompt})
        history2.append({"role": "assistant", "content": reply2})

        return "", history1, style1, history2, style2

    # ---- Bind UI events ----
    msg1.submit(
        ask_and_rewrite,
        [msg1, chatbot1, chatbot2, model1, model2],
        [msg1, chatbot1, style_box1, chatbot2, style_box2]
    )
    clear1.click(lambda: (None, {}, None, {}, None), None,
                 [chatbot1, style_box1, chatbot2, style_box2], queue=False)

demo.launch()
