import google.generativeai as genai
import genslides.utils.loader as Ld
import json 

def geminiGetChatCompletion(msgs, params):
    try:
        print('Try gemini:', params['model'])
        genai.configure(api_key=params['api_key'])


        history = []
        system_instruction = ""
        for message in msgs:
            role = message['role']
            if message['role'] == 'system':
                system_instruction += message['content']
            else:
                if message['role'] == 'assistant':
                    role = 'model'
                msg = message['content']
                history.append({'role': role, 'parts': msg})
        question = history.pop()['parts']
        if system_instruction == "":
            model = genai.GenerativeModel(model_name=params['model'])
        else:
            model = genai.GenerativeModel(model_name=params['model'], system_instruction=system_instruction)
        chat = model.start_chat(history=history)
        if 'response_format' in params and params['response_format'] != "":

            json_schema_init = json.loads(params['response_format'], strict=False)
            try:
                gemini_schema = json_schema_init['json_schema']['schema']
                gemini_schema = Ld.Loader.remove_additional_properties(gemini_schema, "additionalProperties")
            except Exception as e:
                print("Error schema:", e)
                return False, '', {}
            config = genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=gemini_schema)
            response = chat.send_message(question, generation_config=config)
        else:
            response = chat.send_message(question)
        out_param = {
                'intok': response.usage_metadata.prompt_token_count,
                'outtok':response.usage_metadata.candidates_token_count,
                'gemini_system': system_instruction,
                'response_format': params['response_format']
                            }
        msg = response.text
        return True, msg, out_param
    except Exception as e:
        print('Gemini api error=', e) 
        return False, '', {}

