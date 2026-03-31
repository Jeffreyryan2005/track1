import os
from flask import Flask, request, jsonify, render_template_string
from groq import Groq

app = Flask(__name__)

# Configure Groq
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not set")

client = Groq(api_key=GROQ_API_KEY)

# Agent definitions (UNCHANGED)
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

# KEEP YOUR HTML TEMPLATE SAME (no change)
HTML_TEMPLATE = """YOUR SAME HTML HERE (NO CHANGE)"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, agents=AGENTS)

# 🔥 GROQ CHAT
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    agent_key = data.get("agent")
    message = data.get("message", "")

    if not agent_key or agent_key not in AGENTS:
        return jsonify({"error": "Invalid agent"}), 400

    agent = AGENTS[agent_key]

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": agent["system_prompt"]},
                {"role": "user", "content": message}
            ]
        )

        return jsonify({
            "response": response.choices[0].message.content,
            "agent": agent["name"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🔥 GROQ PIPELINE
@app.route("/pipeline", methods=["POST"])
def pipeline():
    data = request.json
    topic = data.get("topic", "")

    if not topic:
        return jsonify({"error": "No topic provided"}), 400

    steps = []
    context = topic

    pipeline_order = ["researcher", "writer", "analyzer", "planner"]

    try:
        for key in pipeline_order:
            agent = AGENTS[key]

            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": agent["system_prompt"]},
                    {"role": "user", "content": context}
                ]
            )

            result = response.choices[0].message.content
            context = result

            steps.append({
                "agent": f"{agent['emoji']} {agent['name']}",
                "response": result
            })

        return jsonify({"steps": steps})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok", "model": "groq-llama3"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)