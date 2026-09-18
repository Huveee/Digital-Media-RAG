# 🤖 P2 Backend Chatbot Server 

A modular **FastAPI-based backend** that powers the **ComAI Chatbot System**, providing an API for an intelligent Bot that behaves based on configuration setup.

---

## 🚀 Overview

This backend serves as the foundation for ComAI’s chatbot infrastructure, offering:
- **One Chatbot Endpoint** (Changes based on Config Setup)
- **Integrated Chat History** (via SQLite)
- **Configuation Setup**

---


## Web Deployment
The latest version of the application is available at:
[comai-p2.apps.informatik.uni-bremen.de/docs](https://comai-p2.apps.informatik.uni-bremen.de/docs)

## Database Access
You can download the **SQLite Database** directly from the server using the following API endpoint:

| Method | Endpoint |
| :--- | :--- |
| **GET** | `https://comai-p2.apps.informatik.uni-bremen.de/admin/db/download?key=FRONTEND_SECRET_KEY` |

> [!IMPORTANT]
> **Action Required:** Replace `FRONTEND_SECRET_KEY` with your actual authorization key before making the request. The request can be made via the url directly in a browser.

---

### Instructions
*   Copy the URL above.
*   Paste it into your browser or a tool like `curl`.
*   Ensure your secret key is kept secure and not shared in public repositories.

## Config Base Setup
- active_bot: str = "llm"           # "llm", "varllm"
- variation_enabled: bool = False   # True/False
- variation_type: str = "metaphor"  # "similarword","hedging","metaphor","style"
- varllm_style: str = "board"       # "joyful","detailed","casual","professional","board"
- llm_model_name: str = "meta-llama-3.1-8b-instruct"    # change to your preferred model from list below
- varllm_model_name: str = "meta-llama-3.1-8b-instruct" # ""

Possible models:
deepseek-r1,meta-llama-3.1-8b-instruct,meta-llama-3.1-8b-rag,llama-3.1-sauerkrautlm-70b-instruct,llama-3.3-70b-instruct
gemma-3-27b-it,mistral-large-instruct,qwen3-235b-a22b,qwen3-32b,openai-gpt-oss-120b

## 🧭 Routes



### `/v1/chat/completions` — Route that communicates with the frontend
**Features:**
- **Setup:** Based on Config
- **Chat History:** Session based: reload or new page => previous context gone

---

## ✍️ Answer Variation Module

Uses an LLM to **rewrite text** according to specific variation parameters.

**Features:**
- **Model:** `Config`
- **Variation Parameters:**  
  - `similarword`  
  - `hedging`  
  - `metaphor`  
  - `style`
- **Manager Function:** Applies the chosen variation type to the given text

---

## 🧰 Tech Stack

| Component | Technology |
|------------|-------------|
| **Framework** | FastAPI |
| **LLMs** | ChatAI-hosted models |
| **Database** | SQLite (`chat_history.db`) |

---



# ✍️ Chat History
  * How it works:
    1. The User askes a prompt: 
        - The Chat has a sessionID.
    2. The prompt is saved in the database with the SessionID.
    3. The generated response is saved in the database with the SessionID.

# 🗂️ Project Structure

* 📁 data
      * fb11_data
      * fb3_data
* 📁 storage *folder for sharing the results via dm-web*
* 📁 Chat_History
      * 🐍chat_history.db *Database for saving the Chathistory using SQLLite*
      * 🐍Chathistorydb.py *Base structure for the Chathistory Database*
* 📁 Chatbots
      * 🐍AnswerGenerator.py *Classes that holds the structure to answer question via rules, llms or rag*
      * 🐍DomainBot.py *Classes for creating the bots for specific domains, including prompts and behaiviour*
      * 🐍Pdf2MarkdownParser.py *PDF to Markdown*
      * 🐍RAGTrainer.py *Trains the RAG Bot*
      * 🐍VariatedLLM.py *A LLM Bot with a few different answer style Prompts*
      * 🐍VariatedPrompts.json *The Prompts for the VarLLM*
      * 🐍VariationGeneration.py *A Bot that rewrites an answer in a different Style based on a given Prompt (Similar Word, Hedging, Metaphor, Style)*
* 📁 Securiy
      * 🐍auth.py *Handels everything regarding to authentication*
      * 🐍userdatabase.py *The database where the user data is stored (username, hashed_password)*
      * 🐍UserModels.py *Base of a user*
* 🐍main.py *File to start the FastAPI Server and connect every modul*
* 🐍requirements.txt *All the requirements that need to be installed*



# Most important Todos
* Config changed in Frontend, access variables then and apply to bots ... -> create a Config with all possible use cases
* Bots should also return it's used sources
* Automatischer Login vom Frontend
* Modularer Aufbau verbessern
* Feedback storing
* Look into SQL relationships --> sql alchemy modul chatbot
* General Testing
* Security (Authentication, HTTPS, Authoriation, Rate Limits, Input Validation, Error Handling) (I have to look up what else can be done)
* Variation Generation where to show
* Chat id change -> create one in frontend?
* Scetch of Communication !!!
* Steaming of answer right now possible?
* Prompt writting easy access
* Update Readme
* Update GitLab Wiki

### Make a virtual environment
```bash
python -m venv modulvenv  
(Linux/MacOS): source modulvenv/bin/activate  | (Win:) .\modulvenv\Scripts\Activate.ps1
pip install --upgrade pip
```
### First, install the packages required to run all the scripts
`
pip install -r requirements.txt
`
  
### To run the chat model with ChatAI API:
Copy the API key from [ChatAI Wiki](https://gitlab.informatik.uni-bremen.de/comai/p2/unimodulchatbot/-/wikis/ChatAI) 
and paste in into the .env file.

### To start the FastAPI Server locally:
`
uvicorn main:app --reload 
`
v1
