from openai import OpenAI
import json

def llamacppGetChatCompletion(msgs, params):
    print('OpenAI get Chat Completion')
    try:
        print('Input params:', params)
        client = OpenAI(
            base_url="http://localhost:8080/v1", # "http://<Your api-server IP>:port"
            api_key = "sk-no-key-required"
        )
        if 'response_format' in params and params['response_format'] != "":
            jformat = json.loads(params['response_format'], strict=False)
            print("With reponse format:",jformat)
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=msgs,
                timeout=7200,
                response_format=jformat
            )
        else:
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=msgs,
                timeout=7200
            )
        
            
        # print('Openai completion=',completion)
        msg = completion.choices[0].message.content
        # print('Out:', msg)
        out_param = {}
        try:
            out_param ['intok'] = completion.usage.prompt_tokens,
            out_param ['outtok'] = completion.usage.completion_tokens
        except:
            pass

        return True, msg, out_param
    except Exception as e:
        print('llama server api error=', e) 
        return False, '', {}
    