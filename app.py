import os
import json
from flask import Flask, request, jsonify, render_template_string
import google.generativeai as genai

app = Flask(__name__)

# Configure Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
genai.configure(api_key=GEMINI_API_KEY)

# Agent definitions
AGENTS = {
    "researcher": {
        "name": "Research Agent",
        "emoji": "🔍",
        "description": "Researches topics and gathers information",
        "system_prompt": "You are a Research Agent. Your job is to thoroughly research any given topic and provide comprehensive, factual information with key insights. Structure your response with: Overview, Key Facts, Important Details, and Summary."
    },
    "writer": {
        "name": "Writer Agent",
        "emoji": "✍️",
        "description": "Writes content based on research",
        "system_prompt": "You are a Writer Agent. Your job is to take information and craft it into well-written, engaging content. Structure your output clearly with proper headings and make it reader-friendly."
    },
    "analyzer": {
        "name": "Analyzer Agent",
        "emoji": "📊",
        "description": "Analyzes data and provides insights",
        "system_prompt": "You are an Analyzer Agent. Your job is to analyze information, identify patterns, trends, and provide actionable insights. Use bullet points and structure your analysis clearly."
    },
    "planner": {
        "name": "Planner Agent",
        "emoji": "📋",
        "description": "Creates plans and strategies",
        "system_prompt": "You are a Planner Agent. Your job is to create detailed, actionable plans and strategies. Break down complex goals into clear steps with timelines and priorities."
    }
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Agent Hub - Track 1</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); min-height: 100vh; color: white; }
        .header { text-align: center; padding: 40px 20px 20px; }
        .header h1 { font-size: 2.5rem; background: linear-gradient(90deg, #4facfe, #00f2fe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .header p { color: #aaa; margin-top: 8px; }
        .badge { display: inline-block; background: linear-gradient(90deg, #4facfe, #00f2fe); color: #000; padding: 4px 14px; border-radius: 20px; font-size: 0.75rem; font-weight: bold; margin-top: 10px; }
        .container { max-width: 1100px; margin: 0 auto; padding: 20px; }
        .agents-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin: 30px 0; }
        .agent-card { background: rgba(255,255,255,0.05); border: 2px solid transparent; border-radius: 16px; padding: 20px; cursor: pointer; transition: all 0.3s; text-align: center; }
        .agent-card:hover { border-color: #4facfe; background: rgba(79,172,254,0.1); transform: translateY(-3px); }
        .agent-card.selected { border-color: #00f2fe; background: rgba(0,242,254,0.15); }
        .agent-emoji { font-size: 2.5rem; margin-bottom: 10px; }
        .agent-name { font-weight: bold; font-size: 1rem; }
        .agent-desc { color: #aaa; font-size: 0.8rem; margin-top: 6px; }
        .chat-area { background: rgba(255,255,255,0.04); border-radius: 16px; padding: 24px; margin-top: 10px; }
        .chat-label { font-size: 1rem; color: #4facfe; margin-bottom: 12px; font-weight: 600; }
        .messages { min-height: 200px; max-height: 400px; overflow-y: auto; margin-bottom: 16px; display: flex; flex-direction: column; gap: 12px; }
        .msg { padding: 14px 18px; border-radius: 12px; line-height: 1.6; font-size: 0.9rem; }
        .msg.user { background: rgba(79,172,254,0.2); border-left: 3px solid #4facfe; align-self: flex-end; max-width: 80%; }
        .msg.agent { background: rgba(0,242,254,0.1); border-left: 3px solid #00f2fe; white-space: pre-wrap; }
        .msg.error { background: rgba(255,80,80,0.2); border-left: 3px solid #ff5050; }
        .input-row { display: flex; gap: 12px; }
        .input-row textarea { flex: 1; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.2); border-radius: 10px; padding: 12px; color: white; font-size: 0.9rem; resize: none; height: 60px; }
        .input-row textarea:focus { outline: none; border-color: #4facfe; }
        .btn { background: linear-gradient(90deg, #4facfe, #00f2fe); color: #000; border: none; border-radius: 10px; padding: 12px 24px; font-weight: bold; cursor: pointer; font-size: 0.9rem; transition: opacity 0.2s; }
        .btn:hover { opacity: 0.85; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .pipeline-section { margin-top: 30px; }
        .pipeline-section h3 { color: #4facfe; margin-bottom: 16px; }
        .pipeline-btn { background: linear-gradient(90deg, #a855f7, #6366f1); color: white; border: none; border-radius: 10px; padding: 12px 24px; font-weight: bold; cursor: pointer; margin-right: 10px; }
        .pipeline-input { width: 100%; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.2); border-radius: 10px; padding: 12px; color: white; font-size: 0.9rem; margin-bottom: 12px; }
        .loading { display: none; color: #4facfe; font-size: 0.85rem; margin-top: 8px; }
        .status-dot { width: 8px; height: 8px; background: #00ff88; border-radius: 50%; display: inline-block; margin-right: 6px; animation: pulse 1.5s infinite; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
    </style>
</head>
<body>
<div class="header">
    <h1>🤖 AI Agent Hub</h1>
    <p>Multi-Agent AI System powered by Google Gemini</p>
    <span class="badge">Track 1 - Build & Deploy AI Agents</span>
</div>
<div class="container">
    <div class="agents-grid" id="agentsGrid">
        {% for key, agent in agents.items() %}
        <div class="agent-card" onclick="selectAgent('{{key}}')" id="card-{{key}}">
            <div class="agent-emoji">{{agent.emoji}}</div>
            <div class="agent-name">{{agent.name}}</div>
            <div class="agent-desc">{{agent.description}}</div>
        </div>
        {% endfor %}
    </div>

    <div class="chat-area">
        <div class="chat-label"><span class="status-dot"></span>Active Agent: <span id="activeAgentLabel">Select an agent above</span></div>
        <div class="messages" id="messages">
            <div class="msg agent">👋 Welcome to AI Agent Hub! Select an agent above and start a conversation. Each agent has specialized capabilities powered by Google Gemini.</div>
        </div>
        <div class="input-row">
            <textarea id="userInput" placeholder="Type your message here..." onkeydown="handleKey(event)"></textarea>
            <button class="btn" onclick="sendMessage()" id="sendBtn">Send ▶</button>
        </div>
        <div class="loading" id="loading">⚡ Agent is thinking...</div>
    </div>

    <div class="pipeline-section">
        <h3>🔗 Multi-Agent Pipeline</h3>
        <p style="color:#aaa; font-size:0.85rem; margin-bottom:12px;">Run a topic through all 4 agents in sequence — Research → Write → Analyze → Plan</p>
        <input class="pipeline-input" id="pipelineInput" placeholder="Enter a topic (e.g. 'Climate Change Solutions')" />
        <button class="pipeline-btn" onclick="runPipeline()">🚀 Run Full Pipeline</button>
        <div class="loading" id="pipelineLoading">⚡ Pipeline running...</div>
        <div id="pipelineResult" style="margin-top:16px;"></div>
    </div>
</div>

<script>
let selectedAgent = null;

function selectAgent(key) {
    selectedAgent = key;
    document.querySelectorAll('.agent-card').forEach(c => c.classList.remove('selected'));
    document.getElementById('card-' + key).classList.add('selected');
    document.getElementById('activeAgentLabel').textContent = document.querySelector('#card-' + key + ' .agent-name').textContent;
}

function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
}

function addMsg(text, type) {
    const div = document.createElement('div');
    div.className = 'msg ' + type;
    div.textContent = text;
    const msgs = document.getElementById('messages');
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
}

async function sendMessage() {
    if (!selectedAgent) { alert('Please select an agent first!'); return; }
    const input = document.getElementById('userInput');
    const text = input.value.trim();
    if (!text) return;
    addMsg(text, 'user');
    input.value = '';
    document.getElementById('sendBtn').disabled = true;
    document.getElementById('loading').style.display = 'block';
    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({agent: selectedAgent, message: text})
        });
        const data = await res.json();
        addMsg(data.response || data.error, data.error ? 'error' : 'agent');
    } catch(e) { addMsg('Error: ' + e.message, 'error'); }
    document.getElementById('sendBtn').disabled = false;
    document.getElementById('loading').style.display = 'none';
}

async function runPipeline() {
    const topic = document.getElementById('pipelineInput').value.trim();
    if (!topic) { alert('Enter a topic first!'); return; }
    document.getElementById('pipelineLoading').style.display = 'block';
    document.getElementById('pipelineResult').innerHTML = '';
    try {
        const res = await fetch('/pipeline', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({topic})
        });
        const data = await res.json();
        let html = '';
        for (const step of data.steps || []) {
            html += `<div style="background:rgba(255,255,255,0.05);border-radius:12px;padding:16px;margin-bottom:12px;border-left:3px solid #4facfe">
                <div style="font-weight:bold;color:#4facfe;margin-bottom:8px">${step.agent}</div>
                <div style="font-size:0.85rem;white-space:pre-wrap;color:#ddd">${step.response}</div>
            </div>`;
        }
        document.getElementById('pipelineResult').innerHTML = html;
    } catch(e) { document.getElementById('pipelineResult').innerHTML = '<div class="msg error">Error: ' + e.message + '</div>'; }
    document.getElementById('pipelineLoading').style.display = 'none';
}
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, agents=AGENTS)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    agent_key = data.get("agent")
    message = data.get("message", "")
    if not agent_key or agent_key not in AGENTS:
        return jsonify({"error": "Invalid agent"}), 400
    if not GEMINI_API_KEY:
        return jsonify({"error": "GEMINI_API_KEY not set. Please add it in environment variables."}), 500
    agent = AGENTS[agent_key]
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=agent["system_prompt"]
        )
        response = model.generate_content(message)
        return jsonify({"response": response.text, "agent": agent["name"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/pipeline", methods=["POST"])
def pipeline():
    data = request.json
    topic = data.get("topic", "")
    if not topic:
        return jsonify({"error": "No topic provided"}), 400
    if not GEMINI_API_KEY:
        return jsonify({"error": "GEMINI_API_KEY not set."}), 500
    steps = []
    context = topic
    pipeline_order = ["researcher", "writer", "analyzer", "planner"]
    prompts = {
        "researcher": f"Research this topic thoroughly: {topic}",
        "writer": f"Based on this research about '{topic}': {context[:500]}... Write an engaging summary.",
        "analyzer": f"Analyze the key insights about '{topic}' from this content: {context[:500]}...",
        "planner": f"Create an action plan based on insights about '{topic}': {context[:300]}..."
    }
    try:
        for key in pipeline_order:
            agent = AGENTS[key]
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=agent["system_prompt"]
            )
            response = model.generate_content(prompts[key])
            result = response.text
            context = result
            steps.append({"agent": f"{agent['emoji']} {agent['name']}", "response": result})
        return jsonify({"steps": steps})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({"status": "ok", "track": 1, "project": "AI Agent Hub"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
