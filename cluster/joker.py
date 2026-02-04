#!/usr/bin/env python3
"""
A single-file Flask app that uses **1 GPU** and a small Hugging Face LLM to generate
short, classroom-safe jokes. Visiting localhost requires providing a topic.

Requirements:
  pip install flask transformers accelerate torch

Run on a cluster compute node (1 GPU allocated):
  export FLASK_APP=joker.py
  flask run --host 0.0.0.0 --port 8000

Then tunnel from your laptop:
  ssh -L 8000:<COMPUTE_NODE>:8000 <user>@mahti.csc.fi

Open:
  http://localhost:8000  -> you must enter a topic to get a joke

Model choice:
  Default: TinyLlama/TinyLlama-1.1B-Chat-v1.0
  Override:
    export JOKE_MODEL="microsoft/phi-2"   (or another small model)
"""

import os
from pathlib import Path

# --- Set Hugging Face cache to CWD ---
HF_CACHE = Path.cwd() / "hf_cache"
HF_CACHE.mkdir(exist_ok=True)

os.environ["HF_HOME"] = str(HF_CACHE)
os.environ["TRANSFORMERS_CACHE"] = str(HF_CACHE)
os.environ["HF_DATASETS_CACHE"] = str(HF_CACHE)
os.environ["HUGGINGFACE_HUB_CACHE"] = str(HF_CACHE)

print(f"[HF cache dir] {HF_CACHE}")

import time
from flask import Flask, request, render_template_string
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# -----------------------
# Config
# -----------------------
MODEL_NAME = os.environ.get("JOKE_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
MAX_NEW_TOKENS = int(os.environ.get("MAX_NEW_TOKENS", "300"))
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0.9"))
TOP_P = float(os.environ.get("TOP_P", "0.95"))

# Force single GPU usage (cuda:0)
if not torch.cuda.is_available():
    raise RuntimeError("CUDA GPU not available. Allocate 1 GPU and run on a compute node.")
torch.cuda.set_device(0)
DEVICE = torch.device("cuda:0")

# -----------------------
# Load model once at startup
# -----------------------
_load_t0 = time.time()
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True,
).to(DEVICE)
model.eval()
torch.cuda.synchronize()
LOAD_SECONDS = time.time() - _load_t0


def build_prompt(topic: str) -> str:
    # Chat-style prompt for TinyLlama; works decently for many chat-tuned small models.
    return (
        "<|system|>\n"
        "You are a witty comedian. Tell short, clean jokes suitable for a classroom.\n"
        "Keep it to less than 400 characters. Avoid offensive content.\n"
        "<|user|>\n"
        f"Tell me a joke about: {topic}\n"
        "<|assistant|>\n"
    )


@torch.inference_mode()
def generate_joke(topic: str) -> str:
    prompt = build_prompt(topic)
    inputs = tokenizer(prompt, return_tensors="pt").to(DEVICE)

    out = model.generate(
        **inputs,
        max_new_tokens=MAX_NEW_TOKENS,
        do_sample=True,
        temperature=TEMPERATURE,
        top_p=TOP_P,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )

    text = tokenizer.decode(out[0], skip_special_tokens=False)

    # Extract assistant answer after the last "<|assistant|>"
    marker = "<|assistant|>"
    if marker in text:
        answer = text.split(marker)[-1]
    else:
        answer = text

    answer = answer.replace("<|endoftext|>", "").strip()
    if "\n\n" in answer:
        answer = answer.split("\n\n")[0].strip()

    return answer

# -----------------------
# Flask app
# -----------------------
app = Flask(__name__)

PAGE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Joke Generator</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem; max-width: 900px; }
    .box { padding: 1rem 1.25rem; border: 1px solid #ddd; border-radius: 12px; }
    input[type=text] { width: 70%; padding: 0.6rem; font-size: 1rem; }
    button { padding: 0.65rem 1rem; font-size: 1rem; cursor: pointer; }
    .muted { color: #666; font-size: 0.95rem; }
    pre { white-space: pre-wrap; word-wrap: break-word; font-size: 1.05rem; }
    .err { color: #b00020; }
  </style>
</head>
<body>
  <h1>GPU Joke Generator</h1>
  <p class="muted">
    Model: <b>{{ model_name }}</b> • Device: <b>{{ device_name }}</b> • Loaded in: <b>{{ load_seconds }}s</b>
  </p>

  <div class="box">
    <form method="get" action="/">
      <label for="topic"><b>Topic</b> (required):</label><br><br>
      <input id="topic" name="topic" type="text" value="{{ topic|e }}" placeholder="e.g., GPUs, Esperanto, coffee" required>
      <button type="submit">Tell me a joke</button>
    </form>

    {% if error %}
      <p class="err"><b>{{ error }}</b></p>
    {% endif %}

    {% if joke %}
      <hr>
      <p><b>Joke ({{ latency }}s):</b></p>
      <pre>{{ joke }}</pre>
    {% endif %}
  </div>

  <p class="muted">
    Tip: You can also call <code>/joke?topic=...</code> to get JSON.
  </p>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def home():
    topic = (request.args.get("topic") or "").strip()

    if not topic:
        # Require a topic: show form, no joke yet
        return render_template_string(
            PAGE,
            model_name=MODEL_NAME,
            device_name=torch.cuda.get_device_name(0),
            load_seconds=f"{LOAD_SECONDS:.2f}",
            topic="",
            joke="",
            latency="",
            error="Please enter a topic to generate a joke.",
        )

    t0 = time.time()
    joke = generate_joke(topic)
    torch.cuda.synchronize()
    latency = time.time() - t0

    return render_template_string(
        PAGE,
        model_name=MODEL_NAME,
        device_name=torch.cuda.get_device_name(0),
        load_seconds=f"{LOAD_SECONDS:.2f}",
        topic=topic,
        joke=joke,
        latency=f"{latency:.2f}",
        error="",
    )


@app.route("/joke", methods=["GET"])
def joke_api():
    topic = (request.args.get("topic") or "").strip()
    if not topic:
        return {"error": "Missing required query parameter: topic"}, 400

    t0 = time.time()
    joke = generate_joke(topic)
    torch.cuda.synchronize()
    latency = time.time() - t0

    return {
        "topic": topic,
        "joke": joke,
        "model": MODEL_NAME,
        "device": torch.cuda.get_device_name(0),
        "latency_seconds": round(latency, 3),
    }


if __name__ == "__main__":
    # Local quick run (will still require GPU)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), debug=True)
