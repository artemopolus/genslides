import json
import requests



def ollamaGetChatCompletion(msgs, params):
    print('ollama get Chat Completion')
    model = params['model']
    r = requests.post(
        "http://127.0.0.1:11434/api/chat",
        json={"model": model, "messages": msgs, "stream": True},
    )
    r.raise_for_status()
    output = ""

    for line in r.iter_lines():
        body = json.loads(line)
        if "error" in body:
            raise Exception(body["error"])
        if body.get("done") is False:
            message = body.get("message", "")
            content = message.get("content", "")
            output += content
            print(content, end="", flush=True)

        if body.get("done", False):
            message["content"] = output

            return True, output, {}
    return False, '', {}
# [[---]]
 