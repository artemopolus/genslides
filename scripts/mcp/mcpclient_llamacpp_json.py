import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# from anthropic import Anthropic
from dotenv import load_dotenv

from openai import OpenAI
import json

load_dotenv()  # load environment variables from .env

def getToolResponse ( request : str, tools : list):
    try:
        client = OpenAI(
                base_url="http://localhost:5000/v1", # "http://<Your api-server IP>:port"
                api_key = "sk-no-key-required"
            )
        
        system_prompt = f"""
            You're a helpful assistant. Analyze my request and choose if you need to use the tool.
        """
        msgs = []
        msgs.append({"role":"system","content":system_prompt})
        msgs.append({"role":"user","content":request})
        completion = client.chat.completions.create(
                    model='model',
                    messages=msgs,
                    timeout=7200,
                    tools=tools,
                    temperature=0.6
                )
        print(f"Response:\n{completion.choices[0]}")
        return completion.choices[0]
    except Exception as e:
        print(f"llama server api error:\n{e}") 
        return ""
 



# def getSimpleResponse( request : str):
#     try:
#         client = OpenAI(
#                 base_url="http://localhost:5000/v1", # "http://<Your api-server IP>:port"
#                 api_key = "sk-no-key-required"
#             )
        
#         system_prompt = f"""
#             You're a helpful assistant. Analyze my request and choose if you need to use the tool.
#         """

#         msgs = []
#         msgs.append({"role":"system","content":system_prompt})
#         msgs.append({"role":"user","content":request})
#         schema = {
#             "type": "json_schema",
#             "json_schema": {
#                 "name": "json_creating",
#                 "schema": {
#                     "type": "object",
#                     "properties": {
#                         "thinking_process":{"type":"string"},
#                         "use_tool":{"type":"boolean"},
#                         "tool_name":{"type":"string"},
#                         "tool_arguments": {
#                             "type": "array",
#                             "items": {
#                                 "type": "object",
#                                 "properties": {
#                                     "argument_name":{"type":"string"},
#                                     "argument_value": {"type": "string"}
#                                 },
#                                 "required": ["argument_name","argument_value"],
#                                 "additionalProperties": False
#                             }
#                         }
#                     },
#                     "required": ["thinking_process","use_tool","tool_name","tool_arguments"],
#                     "additionalProperties": False
#                 },
#                 "strict": True
#             }
#         }

#         completion = client.chat.completions.create(
#                     model='model',
#                     messages=msgs,
#                     timeout=7200,
#                     response_format=schema,
#                     temperature=0.6
#                 )

#         result = completion.choices[0].message.content

#         return result
#     except Exception as e:
#         print(f"llama server api error:\n{e}") 
#         return ""


def getStateFromResponse ( response , scheme : str = "tool"):
    if scheme == "tool":
        if hasattr(response, 'finish_reason'):
            if response.finish_reason == "tool_calls":
                tool_name = response.message.tool_calls[0].function.name
                tool_args = json.loads( response.message.tool_calls[0].function.arguments )
                return "Tool", {"name":tool_name, "args": tool_args, "thinking":""}
            elif response.finish_reason == "stop":
                return "Message", {"thinking": response.message.content}
    elif scheme == "json":
        message = response.message.content
        json_response = json.loads( message )
        if json_response["use_tool"]:
            tool_name = json_response["tool_name"]
            tool_args = json_response["tool_arguments"]
            return "Tool", {"name":tool_name, "args": tool_args, "thinking":json_response["thinking_process"]}
        else:
            return "Message", {"thinking": response.message.content}
    return "None", {}

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        # self.anthropic = Anthropic()

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server
        
        Args:
            server_script_path: Path to the server script (.py or .js)
        """
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

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        response = await self.session.list_tools()
        available_tools = [{ 
            "type":"function",
            "function":{
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        } for tool in response.tools]

        # print(f"Messages:\n{query}\nTools:{available_tools}")

        result = getToolResponse( query, available_tools)

        # Process response and handle tool calls
        final_text = []

        state, pack = getStateFromResponse( result )

        if state == "Tool":
            tool_name = pack["name"]
            tool_args = pack["args"]
            tool_output = await self.session.call_tool(tool_name, tool_args)
            final_text.append(f"Call tool \"{tool_name}\" with arguments:\n{tool_args}\n \
                              Result:\n{tool_output.content[0].text} \
                              \nThinking:{pack["thinking"]}")
        elif state == "Message":
            final_text.append(f"Message:\n{pack["thinking"]}")


        return "\n".join(final_text)

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

