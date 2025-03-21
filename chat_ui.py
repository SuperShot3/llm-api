import gradio as gr
from llama_cpp import Llama
import os

# Load your model
model_path = r"C:\Users\DELL\Model\models\mistral\capybarahermes-2.5-mistral-7b.Q4_K_M.gguf"
llm = Llama(
    model_path=model_path,
    n_ctx=1024,  
    n_threads=os.cpu_count(),
    n_batch=128,
)

# File to store chat history
history_file = "chat_memory.txt"

# Load chat history from file
def load_history():
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as file:
            lines = file.readlines()
            history = []
            for i in range(0, len(lines) - 1, 2):  # Read in pairs
                user = lines[i].strip().replace("User: ", "")
                assistant = lines[i + 1].strip().replace("Assistant: ", "")
                history.append((user, assistant))
            return history
    return []

# Save conversation to history file
def save_to_history(user_message, assistant_response):
    with open(history_file, "a", encoding="utf-8") as file:
        file.write(f"User: {user_message}\nAssistant: {assistant_response}\n\n")

# ✅ Fix: ChatML format for your model
def build_prompt(history, user_message):
    prompt = "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n"

    for user, assistant in history:
        prompt += f"<|im_start|>user\n{user}<|im_end|>\n"
        prompt += f"<|im_start|>assistant\n{assistant}<|im_end|>\n"

    prompt += f"<|im_start|>user\n{user_message}<|im_end|>\n"
    prompt += "<|im_start|>assistant\n"  # Assistant starts responding here

    return prompt

# Chat function (fixes broken responses)
def chat_with_model(message, history=[]):
    prompt = build_prompt(history, message)  # Generate prompt with memory

    result = llm(
        prompt,
        temperature=0.7,
        top_p=0.95,
        top_k=50,
        repeat_penalty=1.1,
        max_tokens=128,
    )
    chunks = llm(prompt, stream=True, max_tokens=64)

    reply = ""
    for chunk in chunks:
        reply += chunk["choices"][0]["text"]

    
    save_to_history(message, reply)  # ✅ Save message to history file

    return reply  # ✅ Return only the reply, NOT a tuple


# Gradio chat interface
chat_interface = gr.ChatInterface(
    fn=chat_with_model,
    title="💬 Local AI Assistant",
    chatbot=gr.Chatbot(),
    textbox=gr.Textbox(placeholder="Ask anything...", lines=1),
    theme="soft",
)

# Load history before starting (so previous chat is visible)
chat_interface.chatbot.history = load_history()

# Launch UI
if __name__ == "__main__":
    chat_interface.launch()
