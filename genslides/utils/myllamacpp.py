from openai import OpenAI
import json
import genslides.utils.loader as Loader

def llamacppGetChatCompletion(msgs, params):
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
        if params.get("tool_for_schema", False):
            tools = getToolFunctionFormat(params.get("tool_default_name","default"), params.get("tool_description",""), params.get("response_format",""))
            return llamacppGetToolResponse(msgs, tools, params)
        if params.get("use_response_format_for_tools", False):
            res, tools = Loader.Loader.loadJsonFromText(params.get("response_format",""))
            if res:
                return llamacppGetToolResponse(msgs, tools, params)
            return False, '', {}

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
                timeout=7200,

            )
        
            
        print('Openai completion\n',completion)
        msg = completion.choices[0].message.content
        choice = completion.choices[0]
        # print('Out:', msg)
        try:
            out_param ['intok'] = completion.usage.prompt_tokens,
            out_param ['outtok'] = completion.usage.completion_tokens
            out_param ['reasoning_content'] = choice.message.reasoning_content
            out_param ['tool_calls'] = choice.message.tool_calls
        except:
            pass

        return True, msg, out_param
    except Exception as e:
        print('llama server api error=', e) 
        return False, '', {}

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
                    temperature= params.get("temperature", 0.6)
                )
        out = {}
        result = completion.choices[0]
        out ['report'] = f"call tool for: {model_name}\n"
        # print(f"Response:\n{completion.choices[0]}")
        if hasattr(result, 'finish_reason'):
            out['finish_reason'] = result.finish_reason
            if result.finish_reason == "tool_calls":
                tool_response_format =  params.get("tool_response_format", "std")
                if tool_response_format == "std":
                    # print("Std tool response format")
                    try:
                        tool_name = result.message.tool_calls[0].function.name
                        tool_args = json.loads( result.message.tool_calls[0].function.arguments )
                    except:
                        pass
                    out['tools'] = Loader.Loader.convJsonToText( [{"name": tool_name, "args": tool_args}] )
                    response = f"Call {tool_name} tool with: {tool_args}"
                elif tool_response_format == "raw":
                    tool_calls_array = result.message.tool_calls
                    response_out = {
                        "content":result.message.content,
                        "reasoning_content": result.message.reasoning_content,
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
                # print("Final data saving")
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
