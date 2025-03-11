import requests
import json

def tabbyApiGetChatCompletion(msgs, params):
    try:
        # Define the API endpoint and headers
        TABBY_API_URL = params.get('url', "http://localhost:5001/v1/chat/completions")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {params['api_key']}" if 'api_key' in params else ""
        }

        # Define the payload for the request
        payload = {
            "model": params.get('model', "gpt-3.5-turbo"),
            "messages": msgs,
        }

        # Add optional parameters to the payload if they are specified
        optional_params = ['max_tokens', 'temperature', 'repetition_penalty', 'top_k', 'top_p']
        for param in optional_params:
            if param in params:
                payload[param] = params[param]

        # Include json_schema if specified and correctly structured
        if 'response_format' in params and params['response_format']:
            jformat = json.loads(params['response_format'], strict=False)
            if jformat.get('type') == 'json_schema' and 'schema' in jformat['json_schema']:
                payload['json_schema'] = jformat['json_schema']['schema']

        # Send the POST request
        response = requests.post(TABBY_API_URL, json=payload, headers=headers)

        # Handle the response
        if response.status_code == 200:
            completion = response.json()
            msg = completion['choices'][0]['message']['content']
            out_param = {}
            try:
                out_param['intok'] = completion['usage']['prompt_tokens']
                out_param['outtok'] = completion['usage']['completion_tokens']
            except KeyError:
                pass
            return True, msg, out_param
        else:
            print(f"API request failed: {response.status_code}, {response.text}")
            return False, '', {}
    except Exception as e:
        print('tabby API error=', e)
        return False, '', {}
