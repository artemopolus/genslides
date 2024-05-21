from openai import OpenAI


def llamacppGetChatCompletion(msgs, params):
    print('OpenAI get Chat Completion')
    try:
        print('Input params:', params)
        client = OpenAI(
            base_url="http://localhost:8080/v1", # "http://<Your api-server IP>:port"
            api_key = "sk-no-key-required"
        )

        completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=msgs,
                timeout=7200
            )
            
        # print('Openai completion=',completion)
        msg = completion.choices[0].message.content
        # print('Out:', msg)
        out_param = {}
        return True, msg, out_param
    except Exception as e:
        print('llama server api error=', e) 
        return False, '', {}
    