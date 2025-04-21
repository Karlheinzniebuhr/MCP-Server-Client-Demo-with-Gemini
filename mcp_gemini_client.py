import asyncio
from typing import Optional, List, Dict, Any
from contextlib import AsyncExitStack
import sys
import os
import json
import logging

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Remove Anthropic import
# from anthropic import Anthropic 
# Add Gemini import
import google.generativeai as genai
# Remove specific type imports that aren't available and use the more generic approach
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

# --- Logging Setup ---
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# File handler for detailed logs
# ---> Change target file back to mcp_log.txt <--- 
file_handler = logging.FileHandler('mcp_log.txt', mode='a') 
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO) # Log INFO level and above to file

# Get the logger for this module
logger = logging.getLogger(__name__) # Use __name__ for the logger
logger.setLevel(logging.INFO) # Set the minimum level for the logger itself
logger.addHandler(file_handler)
# Optional: Add a stream handler to also see logs in the console

logger.info("--- Starting New MCP Client Session (Logging to mcp_log.txt) ---")

# Debug the loaded environment variables
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    # Safely print part of the key
    print(f"Loaded GEMINI_API_KEY: {gemini_key[:5]}... (length: {len(gemini_key)})")
else:
    print("WARNING: GEMINI_API_KEY not found in environment variables!")

# Redirect stdout and stderr to mcp_log.txt
# log_file = open("mcp_log.txt", "a")
# sys.stdout = log_file
# sys.stderr = log_file # Keep this if you still want errors logged

print("Starting MCP Client - Logging to mcp_log.txt")

# Helper to convert MCP Tool Schema to Gemini Tool Schema if needed
# This is a basic conversion, might need adjustments based on complexity
def convert_mcp_tool_to_gemini(mcp_tool: Dict[str, Any]) -> Dict[str, Any]:
    """Converts MCP tool schema to Gemini function declaration."""
    # Assuming mcp_tool['inputSchema'] is a JSON schema dictionary
    properties = mcp_tool.get('inputSchema', {}).get('properties', {})
    required = mcp_tool.get('inputSchema', {}).get('required', [])

    return {
        "name": mcp_tool['name'],
        "description": mcp_tool['description'],
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required,
        }
    }


class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        # Remove Anthropic client
        # self.anthropic = Anthropic()
        # Configure Gemini
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        genai.configure(api_key=gemini_api_key)
        # Initialize Gemini model
        try:
            # Using the simplest form of model creation to avoid compatibility issues
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            print("Successfully created Gemini model")
        except Exception as e:
            print(f"Error creating Gemini model: {e}")
            raise
        
        # Simple history tracking
        self.history = []

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server
        
        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        print(f"Connecting to server script: {server_script_path}") # Log server script path
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
        print("MCP Session Initialized") # Log session initialization
        
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools]) # Log available tools

    async def process_query(self, query: str) -> str:
        """Process a query using Gemini and available tools"""
        if not self.session:
            logger.error("process_query called but MCP session is not initialized.")
            return "Error: MCP session not initialized."
            
        # ---> Comment out the redundant print <--- 
        # print(f"\nUser Query: {query}") 
        logger.info(f"Processing query: '{query[:50]}...'" ) # Use single quotes for clarity
        
        # Add message to history
        self.history.append({"role": "user", "parts": [query]})

        # Get available tools from MCP server
        mcp_tools_response = await self.session.list_tools()
        
        # Get tool descriptions for context
        tool_descriptions = []
        for tool in mcp_tools_response.tools:
            tool_descriptions.append(f"Tool: {tool.name}\nDescription: {tool.description}\nSchema: {json.dumps(tool.inputSchema)}")
        
        tool_context = "\n\n".join(tool_descriptions)
        logger.info(f"Tool context built for prompt (length: {len(tool_context)})") # Log length here is fine
        
        # Create a prompt that instructs the model how to use tools
        prompt = f"""You are an assistant that helps users with weather information.
You have access to the following tools:

{tool_context}

When you need to use a tool, format your response like this:
TOOL_NAME: {{the tool name}}
TOOL_ARGS: {{JSON formatted arguments for the tool}}

Do not include any other text after the tool execution format.
If you don't need a tool, just provide a helpful response.

The user message is: {query}"""
        logger.info(f"=== Prompt Sent to Gemini (Initial) ===\n{prompt}\n======================================")

        logger.info("Sending query to Gemini API...")
        
        try:
            # Make a simple request to Gemini without complex tool definition
            response = await self.model.generate_content_async(prompt)
            
            # Get the text response
            if hasattr(response, 'text'):
                response_text = response.text
            else:
                # Extract text from candidate parts if needed
                response_text = str(response)
                for candidate in getattr(response, 'candidates', []):
                    content = getattr(candidate, 'content', None)
                    if content:
                        for part in getattr(content, 'parts', []):
                            text = getattr(part, 'text', None)
                            if text:
                                response_text = text
                                break
            
            logger.info(f"=== Raw Response Received from Gemini (Initial) ===\n{response_text}\n===============================================")
            
            # Parse the response to check for tool usage
            if "TOOL_NAME:" in response_text and "TOOL_ARGS:" in response_text:
                # Extract tool name and arguments
                tool_name_line = response_text.split("TOOL_NAME:")[1].split("\n")[0].strip()
                tool_args_line = response_text.split("TOOL_ARGS:")[1].strip()
                
                # Remove any markdown formatting
                tool_name = tool_name_line.replace('`', '').strip()
                tool_args_text = tool_args_line.replace('`', '').strip()
                
                try:
                    # Parse the JSON arguments
                    tool_args = json.loads(tool_args_text)
                    
                    logger.info(f"Calling tool: {tool_name} with args: {tool_args}")
                    
                    # Call the MCP tool
                    logger.info(f"Executing MCP tool: {tool_name} with args: {tool_args}")
                    tool_result = await self.session.call_tool(tool_name, tool_args)
                    # --- Log the RAW tool result object received via MCP --- 
                    logger.info(f"Raw MCP Tool Result Object Received: {tool_result}")
                    # --- Extract content for further processing --- 
                    result_content = tool_result.content
                    logger.info(f"MCP tool {tool_name} executed. Extracted Result Content: {str(result_content)[:500]}...") # Log more content
                    
                    # Add tool result to history
                    self.history.append({"role": "assistant", "parts": [f"I need to use the {tool_name} tool"]})
                    self.history.append({"role": "user", "parts": [f"Tool result: {result_content}"]})
                    
                    # Generate final response using the tool result
                    logger.info("Generating final response using tool result...")
                    final_prompt = f"""I asked for information about the weather in response to: "{query}"
                    
I used the {tool_name} tool with these arguments: {json.dumps(tool_args)}
The tool returned this result: {result_content}

Please provide a helpful, user-friendly response based on this information."""
                    logger.info(f"=== Prompt Sent to Gemini (Final) ===\n{final_prompt}\n=======================================")
                    final_response = await self.model.generate_content_async(final_prompt)
                    
                    if hasattr(final_response, 'text'):
                        final_text = final_response.text
                    else:
                        # Extract text from candidate parts if needed
                        final_text = str(final_response)
                        for candidate in getattr(final_response, 'candidates', []):
                            content = getattr(candidate, 'content', None)
                            if content:
                                for part in getattr(content, 'parts', []):
                                    text = getattr(part, 'text', None)
                                    if text:
                                        final_text = text
                                        break
                    logger.info(f"=== Raw Response Received from Gemini (Final) ===\n{final_text}\n===============================================")
                    self.history.append({"role": "assistant", "parts": [final_text]})
                    return final_text
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing tool arguments: {e}", exc_info=True)
                    return f"I tried to use a weather tool, but there was an error with the arguments: {e}. Please try again with a more specific location."
                except Exception as e:
                    logger.error(f"Error calling tool: {e}", exc_info=True)
                    return f"I tried to use the {tool_name} tool, but encountered an error: {e}"
            
            # If no tool was used, just return the response
            return response_text
            
        except Exception as e:
            logger.error(f"Error during Gemini API call: {e}", exc_info=True)
            return f"An error occurred while processing your request with the AI model: {str(e)}"

    async def chat_loop(self):
        """Run an interactive chat loop"""
        logger.info("Starting interactive chat loop.")
        # ---> Update user message about log file <--- 
        print("\nMCP Client Started! Detailed logs in mcp_log.txt") 
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                # ---> Comment out the redundant print <--- 
                # print(f"\nInput Query: {query}") 
                # logger.debug(f"User input received: {query}") # Optional: Log raw input
                
                if query.lower() == 'quit':
                    break
                    
                response = await self.process_query(query)
                print("\nResponse: " + response) # Log final response
                    
            except Exception as e:
                print(f"\nError: {str(e)}") # Log any errors
    
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()
        # Remove check for undefined log_file
        # if log_file:
        #     log_file.close() # Close the log file explicitly

async def main():
    # Setup logging here if you want logs before MCPClient initialization
    if len(sys.argv) < 2:
        # ---> Use logger for usage message if possible, but print is safer before logging is fully confirmed <--- 
        usage_msg = f"Usage: python {sys.argv[0]} <path_to_server_script>"
        print(usage_msg)
        # logger.critical(usage_msg) # Optional: Log critical error if logging is set up early
        sys.exit(1)
    
    logger.info("Client script main execution started.")
    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    except Exception as e:
        print(f"Exception in main: {e}") # Log exceptions in main
    finally:
        await client.cleanup()
        print("MCP Client cleanup completed and exiting") # Log cleanup completion

if __name__ == "__main__":
    import sys
    asyncio.run(main())