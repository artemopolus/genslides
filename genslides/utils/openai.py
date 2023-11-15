from openai import OpenAI


def openaiGetSmplCompletion(messages, params) ->(bool, str, int, int):
    text = ''
    if len(messages) > 1:
        text = messages[-2]['content'] + '\n\n\n'+ messages[-1]['content']
    else:
        text = messages[-1]['content']

    try:
        client = OpenAI(api_key=params['api_key'])
        completion = client.completions.create(
                        model = params['model'],
                        prompt = text,
                        max_tokens= params['max_tokens']
                    )
        msg = completion.choices[0].text
        return True, msg, completion.usage.prompt_tokens, completion.usage.completion_tokens
    except Exception as e:
        print('Open Ai api error=',e) 
        return False, '', 0, 0

def openaiGetChatCompletion(msgs, params):
    try:
        client = OpenAI(api_key=params['api_key'])
        completion = client.chat.completions.create(
            model = params['model'],
            messages=msgs
        )
        msg = completion.choices[0].text
        return True, msg, completion.usage.prompt_tokens, completion.usage.completion_tokens
    except Exception as e:
        print('Open Ai api error=',e) 
        return False, '', 0, 0
    



