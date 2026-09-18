import gradio as gr
from ragbot import RAGBot
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize RAGBot
rag_bot = RAGBot()

# Optionally preload a PDF
#rag_bot.add_pdf("docs/AT-BPO-06-25_Lesefassung_automVerz.pdf")
#rag_bot.add_pdf("docs/AT-MPO-06-25_Lesefassung_automatVerz.pdf")
#rag_bot.add_pdf("docs/BPO-Informatik-VF.pdf")
#rag_bot.add_pdf("docs/MPO_Informatik_VF.pdf")

# UI Logic
def chat(query, history):
    answer, sources, passages, metadatas = rag_bot.ask(query) #Added metadatas
    # format message for Gradio
    if passages:
        formatted_sources = "\n\n---\n\n".join(
            [f"**{src}:** {text}" for src, text in zip(sources, passages)]
        )
        reply = f"{answer}\n\n### Sources:\n{formatted_sources}"
    else:
        reply = answer
    history = history or []
    history.append({"role": "user", "content": query})
    history.append({"role": "assistant", "content": reply})
    return "", history

def user_input(user_message, history):
    reply, sources = rag_bot.ask(user_message)
    history.append({"role": "user", "content": user_message})
    history.append({
        "role": "assistant",
        "content": reply + "\n\n📚 Sources:\n" + "\n".join(sources)
    })
    return "", history


with gr.Blocks() as demo:
    gr.Markdown("## 📚 RAG Chatbot")

    chatbot = gr.Chatbot()
    msg = gr.Textbox(placeholder="Frage mich etwas über Bachelor/Master Studium Informatik...")
    clear = gr.Button("Clear Chat")

    msg.submit(chat, [msg, chatbot], [msg, chatbot])
    clear.click(lambda: ("", []), None, [msg, chatbot], queue=False)

demo.launch()
