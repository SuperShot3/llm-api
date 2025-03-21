from fastapi import FastAPI, Request
from pydantic import BaseModel
from llama_cpp import Llama
import psutil
import time, os
from fastapi.middleware.cors import CORSMiddleware

# Load the AI model
model_path = r"C:\Users\DELL\Model\models\mistral\capybarahermes-2.5-mistral-7b.Q4_K_M.gguf"
llm = Llama(model_path=model_path, n_ctx=2048, n_threads=8)

# Initialize FastAPI
app = FastAPI()

class Query(BaseModel):
    message: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # или конкретный адрес ["http://192.168.1.99"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "LLM API is running. POST to /chat with a message."}

def load_history():
    if os.path.exists("chat_memory.txt"):
        with open("chat_memory.txt", "r", encoding="utf-8") as f:
            return f.read()
    return ""

def save_to_history(user, assistant):
    with open("chat_memory.txt", "a", encoding="utf-8") as f:
        f.write(
            f"<|im_start|>user\n{user}<|im_end|>\n"
            f"<|im_start|>assistant\n{assistant}<|im_end|>\n"
        )

def build_prompt(user_message):
    past = load_history()
    current = f"<|im_start|>user\n{user_message}<|im_end|>\n<|im_start|>assistant\n"
    return "<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n" + past + current

@app.post("/chat")
def chat(query: Query):
    prompt = build_prompt(query.message)

    result = llm(
        prompt,
        max_tokens=128,
        temperature=0.7,
        top_p=0.95,
        top_k=50,
        repeat_penalty=1.1,
    )

    reply = result["choices"][0]["text"].strip()
    save_to_history(query.message, reply)
    return {"response": reply}



@app.middleware("http")
async def log_request_time(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    print(f"Request took {duration:.2f} seconds")
    return response



@app.get("/metrics")
def get_metrics():
    cpu_percent = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    return {
        "cpu_percent": cpu_percent,
        "memory_used_MB": ram.used / 1024 / 1024,
        "memory_percent": ram.percent
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3333)



