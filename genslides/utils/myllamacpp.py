from openai import OpenAI, NotGiven
import json
import genslides.utils.loader as Loader
import requests


def llamacppGetChatCompletion(msgs : list, params : dict):
    # print('LlamaCPP openai api')
    out_param = {}
    out_param ['report'] = f"llamacppGetChatCompletion\n"
    callllamacppreq = params.get("callllamacppreq", False)
    if callllamacppreq:
        return llamacppRawCall( msgs, params, out_param)
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

        tool_for_schema = params.get("tool_for_schema", False)
        use_response_format_for_tools = params.get("use_response_format_for_tools", False)

        append_message_on = params.get("append_messages_reason", "None")
        if append_message_on == "Any" or \
            append_message_on == "Tool" and (tool_for_schema or use_response_format_for_tools) \
            :
            appended_messages_list = params.get("appended_messages_list", [])
            if isinstance( appended_messages_list, str):
                res, add_msgs = Loader.Loader.loadJsonFromText( appended_messages_list )
                if res:
                    appended_messages_list = add_msgs
                else:
                    appended_messages_list = []
            elif isinstance( appended_messages_list, list):
                pass
            else:
                appended_messages_list = []
            for idx, message in enumerate(appended_messages_list):
                if idx == 0 and params.get("unite_appended_messages_with_last", False) \
                    and "role" in message and "content" in message \
                    and "role" in msgs[-1] and "content" in msgs[-1]\
                    and message["role"] == msgs[-1]["role"]:
                    msgs[-1]["content"] += message["content"]
                elif "role" in message and "content" in message:
                    msgs.append( message )

      
        if tool_for_schema:
            tools = getToolFunctionFormat(params.get("tool_default_name","default"), params.get("tool_description",""), params.get("response_format",""))
            return llamacppGetToolResponse(msgs, tools, params)
        if use_response_format_for_tools:
            res, tools = Loader.Loader.loadJsonFromText(params.get("response_format",""))
            if res:
                return llamacppGetToolResponse(msgs, tools, params)
            return False, '', {}
        model_name = getattr(params,'model','unknown')
        out_param ['report'] += f"Standart call: {model_name}\n"

        if 'response_format' in params and params['response_format'] != "":
            jformat = json.loads(params['response_format'], strict=False)
            out_param ['report'] += f"With structured output\n"
            # print("With reponse format:",jformat)
            if 'temperature' in params:
                t = params['temperature']
                out_param ['report'] += f"with temperature{t}\n"
                completion = client.chat.completions.create(
                model=params['model'],
                messages=msgs,
                timeout=7200,
                response_format=jformat,
                temperature=t
            )
            else:
                completion = client.chat.completions.create(
                model=params['model'],
                messages=msgs,
                timeout=7200,
                response_format=jformat
            )
        else:
            out_param ['report'] += f"std msg call\n"
            if 'temperature' in params:
                t = params['temperature']
                out_param ['report'] += f"with temperature{t}\n"
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
                timeout=7200,

            )
        
            
        # print('Openai completion\n',completion)
        msg = completion.choices[0].message.content
        choice = completion.choices[0]
        # print('Out:', msg)
        try:
            out_param ['intok'] = completion.usage.prompt_tokens,
            out_param ['outtok'] = completion.usage.completion_tokens
        except:
            pass
        out_param ['reasoning_content'] = getattr(choice.message,"reasoning_content","")
        out_param ['tool_calls'] = getattr(choice.message,"tool_calls", "")
        out_param ['finish_reason'] = getattr(choice,"finish_reason","error")

        if msg == "":
            out_param ['report'] += f"Empty message\n"
            return False, msg, out_param
        else:
            return True, msg, out_param
    except Exception as e:
        out_param ['report'] += f"llama server api error={e}\n"
        return False, '', out_param

def llamacppGetToolResponse ( msgs : list[str], tools : list, params : dict):
    try:
        # print("llamacppGetToolResponse")
        client = OpenAI(
                base_url= params.get('url', "http://localhost:5000/v1"), # "http://<Your api-server IP>:port"
                api_key = params.get('api_key', "sk-no-key-required")
            )
        
        model_name = params['model']
        completion = client.chat.completions.create(
                    model='model',
                    messages=msgs,
                    timeout=7200,
                    tools=tools,
                    temperature= params.get("temperature", NotGiven)
                )
        out = {}
        result = completion.choices[0]
        out ['report'] = f"call tool for: {model_name}\n"
        response = ""
        # print(f"Response:\n{completion.choices[0]}")
        if hasattr(result, 'finish_reason'):
            out['finish_reason'] = result.finish_reason
            if result.finish_reason == "tool_calls":
                tool_response_format =  params.get("tool_response_format", "std")
                if tool_response_format == "std":
                    out['report'] += "Std tool response format"
                    try:
                        tool_name = result.message.tool_calls[0].function.name
                        tool_args = json.loads( result.message.tool_calls[0].function.arguments )
                    except:
                        out['report'] += "error on tool args"
                        tool_args = {}
                    out['tools'] = Loader.Loader.convJsonToText( [{"name": tool_name, "args": tool_args}] )
                    response = Loader.Loader.convJsonToText( tool_args )
                elif tool_response_format == "raw":
                    tool_calls_array = result.message.tool_calls
                    response_out = {
                        "content":result.message.content,
                        "reasoning_content": getattr(result.message, "reasoning_content", ""),
                        "tool_calls":[]
                    }
                    if tool_calls_array != None:
                        for tool_call in tool_calls_array:
                            response_out["tool_calls"].append({"name":tool_call.function.name,"args":tool_call.function.arguments})
                    response = Loader.Loader.convJsonToText(response_out)
                elif tool_response_format == "tool_args_dict":
                    tool_calls_array = result.message.tool_calls
                    response_out = {}
                    if tool_calls_array != None:
                        for tool_call in tool_calls_array:
                            res, fun_args = Loader.Loader.loadJsonFromText(tool_call.function.arguments)
                            if res:
                                response_out.update( fun_args )
                    response = Loader.Loader.convJsonToText(response_out)
                elif tool_response_format == "tool_args_list":
                    tool_calls_array = result.message.tool_calls
                    response_out = []
                    if tool_calls_array != None:
                        for tool_call in tool_calls_array:
                            res, fun_args = Loader.Loader.loadJsonFromText(tool_call.function.arguments)
                            if res:
                                response_out.append( fun_args )
                    response = Loader.Loader.convJsonToText(response_out)
                out['report'] += "Final data saving"
                out ['tool_content'] = result.message.content
                out ['tool_reasoning_content'] = getattr(result.message, "reasoning_content", "")
                out ['tool_calls_result'] = str(result.message.tool_calls)
            elif result.finish_reason == "stop":
                out ['tool_content'] = result.message.content
                out ['tool_reasoning_content'] = getattr(result.message, "reasoning_content", "")
                out ['tool_calls_result'] = ""
                response = result.message.content
            else:
                out ['tool_content'] = getattr(result.message, "content", "")
                out ['tool_reasoning_content'] = getattr(result.message, "reasoning_content", "")
                out ['tool_calls_result'] = str( getattr(result.message, "tool_calls", ""))
                out['report'] += f"Invalid finish reason:{result.finish_reason}"
                return False, "", out

        return True, response, out
    except Exception as e:
        print(f"llama server api tool error:\n{e}") 
        return False, "", {}

def getToolFunctionFormat( name : str, description : str, schema : str):
    available_tools = []
    final_schema = {}
    res, s = Loader.Loader.loadJsonFromText( schema, True )
    if res:
        if isinstance( s, dict):
            final_schema = s ["json_schema"]["schema"]
        else:
            print(f"not dict:\n{s}")
        available_tools.append({ 
        "type":"function",
        "function":{
            "name": name,
            "description": description,
            "parameters": final_schema
        }}
        )
    else:
        print("No good schemas")
    return available_tools

def llamacppRawCall( msgs : list[dict], params : dict, out_param : dict):
    model_name = params.get('model','unknown')
    out_param ['report'] += f"llamacppRawCall for: {model_name}\n"

    port = params.get('url',"http://127.0.0.1:4085/v1")
    

    url = f"{port}/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer no-key"
    }

    # Тело запроса
    payload = {
        "model": "qwen3.5-35b-a3b",
        "stream": False,
        # Используем тройные кавычки для удобной записи многострочной грамматики GBNF
        "messages": msgs
    }
    allowed_params = ["temperature","top_k","top_p","min_p","grammar","json_schema","chat_template_kwargs"]
    for p in allowed_params:
        if p in params:
            payload[p] = params[p]
            out_param ['report'] += f"Add param {p}"
    if "logit_bias" in params:
        payload["logit_bias"] = {
            "248069": 11.8
        },
    if "grammar" not in params and "json_schema" not in params:
        if "default_grammar" in params:
            payload["grammar"] = params["default_grammar"]
        # payload["grammar"] = "root ::= pre <[248069]> post\npre ::= !<[248069]>*\npost ::= !<[248069]>*",

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Вызовет ошибку, если статус-код не 200
        
        # Вывод результата
        result = response.json()
        choice = result["choices"][0]
        message = choice["message"]
        content = message.get("content","")
        out_param["reasoning_content"] = message.get("reasoning_content","Empty")
        out_param["finish_reason"] = choice.get("finish_reason","No finish reason")
        return True, content, out_param

    except requests.exceptions.RequestException as e:
        out_param ['report'] += f"Ошибка при выполнении запроса: {e}"
        return False, "", out_param
