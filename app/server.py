import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()
app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

html = """
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Chat</title>
    <link rel="icon" href="/static/rocket.png" type="image/png">
</head>
<body>
    <h1>WebSocket Chat</h1>
    <input id="messageInput" type="text" placeholder="Type a message...">
    <button onclick="sendMessage()">Send</button>
    <ul id="messages"></ul>

    <script>
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        var ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

        ws.onmessage = function(event) {
            var li = document.createElement("li");
            li.textContent = event.data;
            document.getElementById("messages").appendChild(li);
        };

        function sendMessage() {
            var input = document.getElementById("messageInput");
            ws.send(input.value);
            input.value = "";
        }
    </script>
</body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8102)
