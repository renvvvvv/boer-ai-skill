import json
import os
import sys
import uuid
import time
import urllib.request
import urllib.error
import urllib.parse
import http.client
import ssl

BASE_URL = "https://www.bohrium.com/bohrapi/v1"
BRM_TOKEN = os.environ.get("BRM_TOKEN", "")

def _headers():
    return {
        "Authorization": f"Bearer {BRM_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "x-bohrium-platform": "h5",
    }

def _request(method, path, params=None, body=None):
    url = f"{BASE_URL}/{path}"
    if params:
        qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items() if v is not None)
        url = f"{url}?{qs}"
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, headers=_headers(), data=data, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"code": e.code, "error": e.read().decode()}
    except Exception as e:
        return {"code": -1, "error": str(e)}

def list_agents():
    result = _request("GET", "sigma-search/api/v3/agent/list")
    agents = result.get("data", {}).get("agents", [])
    output = []
    for a in agents:
        models = a.get("models", [])
        model_info = "; ".join(f"{m['model']}({m.get('photonPrice',0)}光子)" for m in models) if models else "无"
        output.append({
            "id": a["id"],
            "name": a.get("nameCn", a.get("nameEn", "")),
            "description": a.get("descriptionCn", a.get("descriptionEn", "")),
            "models": model_info,
            "placeholder": a.get("placeholderCn", a.get("placeholderEn", "")),
        })
    return output

def chat(agent_id, message, session_id=None, model="auto", scene="paper"):
    if not BRM_TOKEN:
        return {"error": "BRM_TOKEN environment variable not set"}
    if not session_id:
        session_id = str(uuid.uuid4())

    create_result = _request("POST", "square/question/create", body={
        "sessionId": session_id,
        "agentId": agent_id,
        "scene": scene,
        "title": message[:50],
    })
    if create_result.get("code") != 0:
        return create_result

    local_msg_id = str(uuid.uuid4())
    chat_payload = {
        "SNPReq": {
            "sessionId": session_id,
            "channel": {
                "schema": "fe", "version": "v1", "agent": "", "branchId": "",
                "sourceSessionId": "", "sourceQuestionId": "", "questionId": "",
                "answerId": "", "messageId": str(uuid.uuid4()),
                "role": "user", "auth": 1,
                "uiInfo": {
                    "localMessageId": local_msg_id, "layout": "main", "type": "ui",
                    "subType": "@bohrium-chat/common/markdown",
                    "content": {"text": message},
                    "response": {}, "actionList": [{"key": "text", "action": "append"}]
                },
                "entities": [], "state": {}, "meta": {}
            },
            "system": {
                "payload": {
                    "model": model, "agentId": agent_id, "sessionId": session_id,
                    "scene": scene, "streaming": True,
                    "biz": {}
                }
            },
            "snp_version": "1.0.0"
        }
    }
    chat_result = _request("POST", "sigma-search/api/v3/session/chat_agent", body=chat_payload)
    if chat_result.get("code") != 0:
        return chat_result

    time.sleep(1)
    parsed = urllib.parse.urlparse(f"{BASE_URL}/sigma-search/api/v3/sse/ai_search/v1/{session_id}/stream")
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(parsed.hostname, context=ctx, timeout=120)
    conn.request("GET", parsed.path, headers={
        'Authorization': f'Bearer {BRM_TOKEN}',
        'Accept': 'text/event-stream, text/event-stream',
        'User-Agent': 'Mozilla/5.0',
        'x-bohrium-platform': 'h5',
    })
    resp = conn.getresponse()
    buffer = b""
    while True:
        try:
            chunk = resp.read(4096)
            if not chunk:
                break
            buffer += chunk
        except Exception:
            break
    conn.close()

    text = buffer.decode('utf-8', errors='replace')
    events = []
    for line in text.split("\n"):
        if line.startswith("data:"):
            try:
                events.append(json.loads(line[5:]))
            except:
                pass

    return {"session_id": session_id, "events": events}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Bohrium AI Chat Skill")
    parser.add_argument("action", choices=["list_agents", "chat"], help="Action to perform")
    parser.add_argument("--agent", default="sn", help="Agent ID (default: sn)")
    parser.add_argument("--message", help="Message to send")
    parser.add_argument("--session", help="Session ID for continuing conversation")
    parser.add_argument("--model", default="auto", choices=["auto", "pro", "deepthink"], help="Model selection")
    parser.add_argument("--scene", default="paper", help="Scene (paper, scholar_QA, writing, patent, general)")
    args = parser.parse_args()

    if args.action == "list_agents":
        agents = list_agents()
        print(json.dumps(agents, indent=2, ensure_ascii=False))
    elif args.action == "chat":
        if not args.message:
            print("Error: --message is required for chat action")
            sys.exit(1)
        result = chat(args.agent, args.message, args.session, args.model, args.scene)
        print(json.dumps(result, indent=2, ensure_ascii=False))