import asyncio
import json
import os

# Force matplotlib to use the non-interactive 'Agg' backend to avoid GUI errors.
os.environ["MPLBACKEND"] = "Agg"

from typing import Any, AsyncIterator, Dict

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Load environment variables
load_dotenv()
app = FastAPI()

# Mount the static files directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AgenticX: Playground</title>
  <link rel="icon" href="/static/rocket.png" type="image/png">
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <link rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
        integrity="sha512-XxZY1F1..."
        crossorigin="anonymous"
        referrerpolicy="no-referrer" />
  <!-- Include highlight.js and its stylesheet -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/atom-one-dark.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>
  <!-- Custom CSS for console-like styling -->
  <style>
    pre code {
      display: block;
      padding: 1rem;
      background-color: #2d2d2d;
      color: #f8f8f2;
      border-radius: 8px;
      overflow-x: auto;
      font-family: "Fira Code", monospace;
      white-space: pre-wrap;
    }
  </style>
  <script>
    // Configure marked to use highlight.js for code blocks
    marked.setOptions({
      highlight: function(code, lang) {
        if (lang && hljs.getLanguage(lang)) {
          return hljs.highlight(code, { language: lang }).value;
        }
        return hljs.highlightAuto(code).value;
      }
    });
  </script>
</head>
<body class="bg-white flex flex-col min-h-screen">
  <!-- Messages Container -->
  <main class="flex-1 overflow-y-auto p-4">
    <div class="max-w-3xl mx-auto">
      <ul id="messages" class="space-y-6">
        <!-- Messages will be inserted here -->
      </ul>
    </div>
  </main>

  <!-- Input Container with black top border and white background -->
  <div class="border-t-2 border-black bg-white p-4">
    <div class="max-w-3xl mx-auto">
      <div class="flex items-center space-x-2 bg-white rounded-xl border border-black shadow-lg p-2">
        <button class="p-2 border border-black rounded-lg hover:bg-black hover:text-white transition-colors">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" class="text-black">
            <path d="M12 4V20M4 12H20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
        <input id="messageInput"
               type="text"
               placeholder="Message ChatGPT..."
               class="flex-1 px-3 py-2 outline-none text-black"
               autofocus>
        <button onclick="sendMessage()"
                class="bg-black text-white px-4 py-2 rounded-lg border border-black transition-colors hover:bg-white hover:text-black flex items-center space-x-2">
          <span>Send</span>
        </button>
      </div>
    </div>
  </div>

  <script>
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
    
    function formatStepData(data) {
      let html = '<div class="bg-white rounded-lg border border-gray-200 shadow-sm p-6">';
      
      // Assistant header
      html += `
        <div class="flex items-start space-x-4 mb-4">
          <div class="w-8 h-8 bg-black rounded-full flex items-center justify-center">
            <i class="fas fa-robot text-white text-sm"></i>
          </div>
          <div class="flex-1">
            <div class="flex items-center space-x-2">
              <span class="font-medium text-gray-900">Assistant</span>
              <span class="text-gray-500 text-sm">${new Date().toLocaleTimeString()}</span>
            </div>
          </div>
        </div>`;

      // The agent is expected to return markdown that includes fenced code blocks.
      if (data.final_answer) {
        html += `<div class="prose max-w-none">${marked.parse(data.final_answer)}</div>`;
      }
      
      if (data.error) {
        html += `
          <div class="mt-2 p-3 bg-red-50 text-red-700 rounded-md">
            <div class="font-medium">Error</div>
            <div class="text-sm">${data.error}</div>
          </div>`;
      }

      if (data.tool_calls) {
        html += `
          <div class="mt-2">
            <div class="font-medium text-gray-700 mb-2">Tool Calls</div>
            ${data.tool_calls.map(tool => `
              <div class="bg-gray-50 rounded p-3 mb-2">
                <div class="text-sm font-medium text-gray-700">${tool.name}</div>
                <pre class="mt-1 text-sm text-gray-600 overflow-x-auto">${tool.arguments}</pre>
              </div>
            `).join('')}
          </div>`;
      }

      if (data.observations) {
        html += `
          <div class="mt-2">
            <div class="font-medium text-gray-700 mb-2">Observations</div>
            <div class="bg-gray-50 rounded p-3">
              <pre class="text-sm text-gray-600 overflow-x-auto">${data.observations}</pre>
            </div>
          </div>`;
      }

      if (data.duration) {
        html += `
          <div class="mt-4 text-sm text-gray-500">
            Execution time: ${data.duration.toFixed(2)}s
          </div>`;
      }

      html += '</div>';
      return html;
    }

    function formatUserMessage(message) {
      return `
        <div class="flex items-start space-x-4 mb-4">
          <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
            <i class="fas fa-user text-white text-sm"></i>
          </div>
          <div class="flex-1">
            <div class="flex items-center space-x-2">
              <span class="font-medium text-gray-900">You</span>
              <span class="text-gray-500 text-sm">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="mt-1 text-gray-800">${message}</div>
          </div>
        </div>`;
    }

    ws.onmessage = function(event) {
      const messages = document.getElementById("messages");
      const li = document.createElement("li");
      try {
        const data = JSON.parse(event.data);
        li.innerHTML = formatStepData(data);
      } catch (e) {
        li.innerHTML = formatStepData({ final_answer: event.data });
      }
      
      messages.appendChild(li);
      // Re-highlight all code blocks after inserting new content
      hljs.highlightAll();
      window.scrollTo(0, document.body.scrollHeight);
    };

    function sendMessage() {
      const input = document.getElementById("messageInput");
      const message = input.value.trim();
      if (message !== "") {
        const messages = document.getElementById("messages");
        const li = document.createElement("li");
        li.innerHTML = formatUserMessage(message);
        messages.appendChild(li);
        ws.send(message);
        input.value = "";
        window.scrollTo(0, document.body.scrollHeight);
      }
    }

    document.getElementById("messageInput").addEventListener("keypress", function(e) {
      if (e.key === "Enter") {
        sendMessage();
      }
    });
  </script>
</body>
</html>
"""

# --- Integration with smolagents ---
from smolagents import CodeAgent, LiteLLMModel

# Initialize the model (example using "claude-3-5-sonnet-20240620")
model = LiteLLMModel(model_id="claude-3-5-sonnet-20240620")
# Create an instance of CodeAgent with extended authorized imports.
agent = CodeAgent(
    tools=[],
    model=model,
    add_base_tools=True,
    additional_authorized_imports=[
        "pandas",
        "openpyxl",
        "xlrd",
        "os",
        "matplotlib",
        "np",
        "statsmodels",
        "numpy",
    ],
)


async def async_stream_data(prompt: str) -> AsyncIterator[Dict]:
    """
    Generate streaming step data from the agent. It iterates over each step yielded
    by agent.run (with stream=True), converts them into serializable dictionaries,
    and yields each for the websocket.
    """
    loop = asyncio.get_running_loop()
    iter_steps = iter(agent.run(prompt, stream=True))
    sentinel = object()  # Unique sentinel for exhaustion
    while True:
        step = await loop.run_in_executor(None, lambda: next(iter_steps, sentinel))
        if step is sentinel:
            break

        print(step)

        step_data = {
            "type": "step",
            "step_number": getattr(step, "step", None),
            "duration": getattr(step, "duration", None),
            "error": (
                str(getattr(step, "error", None))
                if getattr(step, "error", None)
                else None
            ),
            "observations": getattr(step, "observations", None),
            "action_output": getattr(step, "action_output", None),
            "agent_memory": getattr(step, "agent_memory", None),
            "tool_calls": (
                [
                    {
                        "name": tool_call.name,
                        "arguments": tool_call.arguments,
                        "id": tool_call.id,
                    }
                    for tool_call in getattr(step, "tool_calls", [])
                ]
                if hasattr(step, "tool_calls") and step.tool_calls
                else None
            ),
            "start_time": getattr(step, "start_time", None),
            "end_time": getattr(step, "end_time", None),
            "llm_output": getattr(step, "llm_output", None),
            "final_answer": getattr(step, "final_answer", None),
        }
        yield step_data


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        prompt = await websocket.receive_text()
        async for step_data in async_stream_data(prompt):
            await websocket.send_text(json.dumps(step_data))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8102)
