#!/usr/bin/env python3
"""Démo agent d'astreinte

Boucle simple et fiable pour un modèle local (27B) servi en API compatible
OpenAI via llama.cpp server.

Protocole texte (plus fiable que le JSON pour un petit modèle) :
- Le modèle nomme un outil (ex: "check_disk") puis Python l'exécute et lui
  renvoie le résultat.
- Le modèle a fini quand il répond "RAPPORT: ..." puis Python s'arrête.

Utilisation :
    AGENT_MODEL=modele python3 agent.py
"""

import json
import os
import re
import urllib.request

import tools

BASE_URL = os.environ.get("LLM_BASE_URL", "http://127.0.0.1:8080")
MODEL = os.environ.get("AGENT_MODEL", "/etc/llama/models/qwen3.8-27b-q3.gguf")

TOOLS = {
    "check_disk": tools.check_disk,
    "check_service": tools.check_service,
    "read_logs": tools.read_logs,
    "clean_temp": tools.clean_temp,
    "restart_service": tools.restart_service,
}

PROMPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "system_prompt.txt")

def load_system_prompt():
    with open(PROMPT_PATH, encoding="utf-8") as f:
        return f.read()

def call_llm(messages):
    url = f"{BASE_URL.rstrip('/')}/v1/chat/completions"
    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "temperature": 0.1,
        "max_tokens": 512,
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]

def find_tool(text):
    for name in TOOLS:
        if re.search(rf"\b{name}\b", text):
            return name
    return None

def main():
    messages = [
        {"role": "system", "content": load_system_prompt()},
        {"role": "user", "content":
            "Le serveur test-almalinux est en alerte. "
            "Diagnostique et répare, puis fais un rapport."},
    ]
    print("=" * 55)
    print("AGENT D'ASTREINTE - modèle :", MODEL)
    print("=" * 55)
    print("[user]", messages[1]["content"])

    for step in range(1, 9):
        print(f"\n--- étape {step} : le modèle décide ---")
        try:
            reply = call_llm(messages)
        except Exception as e:
            print("[erreur API]", e)
            break
        messages.append({"role": "assistant", "content": reply})
        print("[assistant]", reply)

        if re.search(r"\bRAPPORT\s*:", reply):
            print("\n=== RAPPORT FINAL ===")
            print(reply)
            break

        tool = find_tool(reply)
        if tool is None:
            messages.append({
                "role": "user",
                "content": "Nomme exactement UN outil parmi : "
                           + ", ".join(TOOLS) + ".",
            })
            print("[système] (aucun outil détecté, je redemande)")
            continue

        result = TOOLS[tool]()
        print(f"[outil] {tool} -> {result}")
        messages.append({"role": "user", "content": f"Résultat de {tool} :\n{result}"})
    else:
        print("\n[fin] limite d'étapes atteinte.")

if __name__ == "__main__":
    main()
