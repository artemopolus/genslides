import google.generativeai as genai

def geminiGetChatCompletion(msgs, params):
    try:
        print('Try gemini:', params['model'])
        genai.configure(api_key=params['api_key'])

        model = genai.GenerativeModel(model_name=params['model'])

        history = []
        for message in msgs:
            role = message['role']
            if message['role'] == 'assistant':
                role = 'model'
            msg = message['content']
            history.append({'role': role, 'parts': msg})
        question = history.pop()['parts']
        chat = model.start_chat(history=history)
        response = chat.send_message(question)
        out_param = {
                'intok': response.usage_metadata.prompt_token_count,
                'outtok':response.usage_metadata.candidates_token_count
                            }
        msg = response.text
        return True, msg, out_param
    except Exception as e:
        print('Gemini api error=', e) 
        return False, '', {}

