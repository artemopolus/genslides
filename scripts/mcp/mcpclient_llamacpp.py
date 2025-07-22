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
 


class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        # self.anthropic = Anthropic()

    async def connect_to_server(self, command : str, server_script_path: str):
        """Connect to an MCP server
        
        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        is_ts = server_script_path.endswith('.ts')
        if not (is_python or is_js or is_ts):
            raise ValueError("Server script must be a .py or .js file")
            
        # command = "python" if is_python else "node"
        if is_ts:
            server_params = StdioServerParameters(
                command=command,
                args=[server_script_path],
                env=None
            )
        else:
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
        final_text = []
        available_tools = [{ 
            "type":"function",
            "function":{
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        } for tool in response.tools]

        # print(f"Messages:\n{query}\nTools:{available_tools}")

        if True:
            for tool in available_tools:
                print(tool)
        else:

            result = getToolResponse( query, available_tools)

            # Process response and handle tool calls

            if hasattr(result, 'finish_reason'):
                if result.finish_reason == "tool_calls":
                    tool_name = result.message.tool_calls[0].function.name
                    tool_args = json.loads( result.message.tool_calls[0].function.arguments )
                    tool_output = await self.session.call_tool(tool_name, tool_args)
                    final_text.append(f"Call tool \"{tool_name}\" with arguments:\n{tool_args}\nResult:\n{tool_output.content[0].text}")

                elif result.finish_reason == "stop":
                    final_text.append(f"Message:\n{result.message.content}")

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
    if len(sys.argv) < 3:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)
        
    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1], sys.argv[2])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())

