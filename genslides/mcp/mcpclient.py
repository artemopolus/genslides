import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import genslides.utils.llmodel as Llmodel
# from mcp.client.sse import sse_client

# from anthropic import Anthropic
from dotenv import load_dotenv
import json

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server
        
        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        print(f"Connect to server by path:{server_script_path}")
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")
            
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        await self.session.initialize()
        
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query_with_so(self, messages : list[dict], model_parameters : dict, mcp_parameters : dict):
        print("Process query with SO")
        param = {}
        response = await self.session.list_tools()

        tools_text = ""
        tools_list = []
        resp_form_txt = model_parameters.get("response_format","")
        if resp_form_txt == "":
            so_schema = {"type":"json_schema","json_schema":{
                "name":"tool_json_template",
                "schema":{
                    "type":"object",
                    "properties":{
                        "tool_calls":{
                            "type": "object",
                            "properties":{},
                            "required":[],
                            "additionalProperties": False
                        }
                    },
                    "required":["tool_calls"],
                    "additionalProperties": False
                    },
                    "strict":True
                }
            }
        else:
            so_schema = json.loads(resp_form_txt)

        if "jsonkeyspath" in mcp_parameters:
            path_input = mcp_parameters["jsonkeyspath"].split(",")
        else:
            path_input = ["json_schema","schema","properties","tool_calls","properties"]
        so_schema_input = so_schema
        for key in path_input:
            if key in so_schema_input:
                so_schema_input = so_schema_input[key]
            else:
                return False, "", {}

        # so_schema_input = so_schema["json_schema"]["properties"]
        filter_fun_on = False
        if "include_functions" in mcp_parameters and mcp_parameters["include_functions"] != "ALL":
            filter_fun_on = True
            function_names = mcp_parameters["include_functions"].split(",")

        for tool in response.tools:
            if ( filter_fun_on and tool.name in function_names ) or not filter_fun_on:
                so_schema_input.update({
                    tool.name : tool.inputSchema
                })
                tools_text += f"# {tool.name}\n{tool.description}\n\n"
            # if filter_fun_on:
                # if tool.name in function_names:
                    # tools_list.append(tool.name)
            # else:
                tools_list.append(tool.name)

        model_parameters["response_format"] = json.dumps(so_schema)

        chat = Llmodel.LLModel(model_parameters)
        messages.append({
            "content": tools_text,
            "role":"user"
        })

        res, resp, param = chat.createChatCompletion( messages )
        
        param["response_format"] = so_schema
        param["tools_description"] = tools_text
        param["tools_list"] = ",".join(tools_list)
        return res, resp, param

    async def process_query(self, messages : list[dict], parameters : dict):
        """Process a query using Claude and available tools"""
        print("Process query")
        response = await self.session.list_tools()

        available_tools = []
        tools_text = ""
        for tool in response.tools:
            available_tools.append({ 
            "type":"function",
            "function":{
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }}
            )
            tools_text += f"# {tool.name}\n{tool.description}\n\n"

        chat = Llmodel.LLModel(parameters)
        res, msg, param = chat.createToolCalling( messages, available_tools )
        param["tools_description"] = tools_text
        return res, msg, param
        # return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                    
                response = await self.process_query(query)
                print("\n" + response)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)
        
    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())

