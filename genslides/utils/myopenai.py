from openai import OpenAI


def openaiGetSmplCompletion(messages, params) ->(bool, str, int, int):
    print('OpenAI get Completion')
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
    print('OpenAI get Chat Completion')
    try:
        print('Input params:', params)
        client = OpenAI(api_key=params['api_key'])
        # print(params['api_key'])
        # print('Target model=',params['model'])
        # print('Msgs:', msgs)
        logprobs = params['logprobs'] if 'logprobs' in params else False
        top_logprobs = params['top_logprobs'] if 'top_logprobs' in params else 0
        if 'logprobs' in params and params['logprobs'] and 'temperature' in params:
            print('Get with logprobs and temperature')
            completion = client.chat.completions.create(
                model = params['model'],
                messages=msgs,
                logprobs=logprobs,
                top_logprobs=top_logprobs,
                temperature=params['temperature']
            )
        elif 'logprobs' in params and params['logprobs']:
            print('Get with logprobs')
            completion = client.chat.completions.create(
                model = params['model'],
                messages=msgs,
                logprobs=logprobs,
                top_logprobs=top_logprobs
            )
        else:
            print('Get simple')
            completion = client.chat.completions.create(
                model = params['model'],
                messages=msgs
            )
        # print('Openai completion=',completion)
        msg = completion.choices[0].message.content
        # print('Out:', msg)
        # print('Msg=',completion.choices[0].message)
        # print('logprobs=',completion.choices[0].logprobs)
        out_param = {
            'intok': completion.usage.prompt_tokens,
            'outtok':completion.usage.completion_tokens
                     }
        if 'logprobs' in params and params['logprobs']:
            # out_param['logprobs'] = completion.choices[0].logprobs.content
            c = completion.choices[0].logprobs.content
            log = []
            for val in c:
                top = val.top_logprobs
                l = []
                for t in top:
                    l.append({
                        'token':t.token,
                        'log_prob': t.logprob,
                        'bytes' : t.bytes
                    })
                log.append({
                    'token':val.token,
                    'logprob':val.logprob,
                    'top_logprobs': l
                        })
            out_param['logprobs'] =  log       
        # print(out_param)    
        return True, msg, out_param
    except Exception as e:
        print('Open Ai api error=', e) 
        return False, '', {}
    



