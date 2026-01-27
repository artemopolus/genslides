from openai import OpenAI
import json

def openrouterGetChatCompletion(msgs, params):
    # print('LlamaCPP openai api')
    try:
        # print('Input params:', params)
        try:
            client = OpenAI(
            base_url=params['url'], # "http://<Your api-server IP>:port"
            api_key = params['api_key']
        )
        except:
            client = OpenAI(
            base_url="http://localhost:8080/v1", # "http://<Your api-server IP>:port"
            api_key = "sk-no-key-required"
        )
        out_param = {}
        if 'response_format' in params and params['response_format'] != "":
            jformat = json.loads(params['response_format'], strict=False)
            # print("With reponse format:",jformat)
            if 'temperature' in params:
                completion = client.chat.completions.create(
                model=params['model'],
                messages=msgs,
                timeout=7200,
                response_format=jformat,
                temperature=params['temperature']
            )
            else:
                completion = client.chat.completions.create(
                model=params['model'],
                messages=msgs,
                timeout=7200,
                response_format=jformat
            )
        else:
            if 'temperature' in params:
                completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=msgs,
                timeout=7200,
                temperature=params['temperature']
            )
            else:
                completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=msgs,
                timeout=7200
            )
        
            
        # print('Openai completion\n',completion)
        msg = completion.choices[0].message.content
        # print('Out:', msg)
        try:
            out_param ['intok'] = completion.usage.prompt_tokens,
            out_param ['outtok'] = completion.usage.completion_tokens
        except:
            pass

        return True, msg, out_param
    except Exception as e:
        print('llama server api error=', e) 
        return False, '', {}

def openrouterGetToolResponse ( msgs : list[str], tools : list, params : dict):
    try:
        client = OpenAI(
                base_url= params.get('url', "http://localhost:5000/v1"), # "http://<Your api-server IP>:port"
                api_key = params.get('api_key', "sk-no-key-required")
            )
        
        completion = client.chat.completions.create(
                    model='model',
                    messages=msgs,
                    timeout=7200,
                    tools=tools,
                    temperature= params.get("temperature", 0.6)
                )
        out = {}
        result = completion.choices[0]
        # print(f"Response:\n{completion.choices[0]}")
        if hasattr(result, 'finish_reason'):
            if result.finish_reason == "tool_calls":
                out['finish_reason'] = "tool_call"
                tool_name = result.message.tool_calls[0].function.name
                tool_args = json.loads( result.message.tool_calls[0].function.arguments )
                out['tools'] = [{"name": tool_name, "args": tool_args}]
                response = f"Call {tool_name} tool with: {tool_args}"
            elif result.finish_reason == "stop":
                out['finish_reason'] = "message"
                response = result.message.content
            else:
                return False, "", {}

        return True, response, out
    except Exception as e:
        print(f"llama server api error:\n{e}") 
        return False, "", {}
 