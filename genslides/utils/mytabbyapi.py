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
        out_param = {}
        for param in optional_params:
            if param in params:
                payload[param] = params[param]
                
                out_param[param] = params[param]

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
            try:
                out_param['intok'] = completion['usage']['prompt_tokens']
                out_param['outtok'] = completion['usage']['completion_tokens']
            except KeyError:
                pass
            return True, msg, out_param
        else:
            print(f"API request failed: {response.status_code}, {response.text}")
            return False, '', out_param
    except Exception as e:
        print('tabby API error=', e)
        return False, '', out_param

def tabbyapi_num_tokens_from_text( text, params ):
    TABBY_API_URL = params.get('url', "http://localhost:5001/v1/token/encode")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {params['api_key']}" if 'api_key' in params else ""
    }

    # Define the payload for the request
    payload = {
        "add_bos_token": True,
        "encode_special_tokens": True,
        "decode_special_tokens": True,
        "text": text
    }
    response = requests.post(TABBY_API_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        completion = response.json()
        msg = completion["length"]
        return True, msg
    else:
        print(f"API request failed: {response.status_code}, {response.text}")
        return False, 0

def tabbyapi_get_model( params ):
    TABBY_API_URL = params.get('url', "http://localhost:5001/v1/model")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {params['api_key']}" if 'api_key' in params else ""
    }
    response = requests.get(TABBY_API_URL, headers=headers)
    if response.status_code == 200:
        completion = response.json()
        return True, completion
    else:
        print(f"API request failed: {response.status_code}, {response.text}")
        return False, {}

def tabbyapi_switch_model( params ):
    if tabbyapi_unload_model(params):
        return tabbyapi_load_model( params )
    return False, {}

def tabbyapi_load_model( params ):
    TABBY_API_URL = params.get('url', "http://localhost:5001/v1/model/load")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {params['api_key']}" if 'api_key' in params else ""
    }

    # Define the payload for the request
    payload = {
        "model_name": params.get("id", ""),
        "max_seq_len": params.get("max_seq_len", 4096),
        "cache_size": params.get("cache_size", 4096),
        "vision": False
    }
    response = requests.post(TABBY_API_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        completion = response.json()
        return True, completion
    else:
        print(f"API request failed: {response.status_code}, {response.text}")
        return False, {}


def tabbyapi_unload_model( params ):
    TABBY_API_URL = params.get('url', "http://localhost:5001/v1/model/unload")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {params['api_key']}" if 'api_key' in params else ""
    }
    response = requests.get(TABBY_API_URL, headers=headers)
    
    if response.status_code == 200:
        return True
    else:
        print(f"API request failed: {response.status_code}, {response.text}")
        return False


