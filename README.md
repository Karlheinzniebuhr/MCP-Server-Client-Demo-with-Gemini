**TL;DR / Resumen**

1.  Instala dependencias: `pip install -r requirements.txt`
2.  Crea `.env` con `GEMINI_API_KEY=TU_CLAVE_API_AQUI`.
3.  Ejecuta: `python mcp_gemini_client.py weather_tool_server.py`

---

**TL;DR / Summary**

1.  Install deps: `pip install -r requirements.txt`
2.  Create `.env` with `GEMINI_API_KEY=YOUR_API_KEY_HERE`.
3.  Run: `python mcp_gemini_client.py weather_tool_server.py`

---

# Proyecto Cliente MCP con Gemini y Servidor de Herramientas Meteorológicas

Este repositorio demuestra cómo usar el protocolo MCP (Model-Client-Protocol) para conectar un cliente de IA (usando Google Gemini) con un servidor que proporciona herramientas especializadas (en este caso, herramientas meteorológicas).

## Cómo Funciona

El sistema actúa como un puente entre la IA de Gemini y las herramientas especializadas. Aquí está el flujo explicado de forma sencilla:

### Roles de los Componentes

1.  **`mcp_gemini_client.py`** - Este es el "intermediario" que:
    *   Habla con la IA de Gemini.
    *   Se conecta al servidor de herramientas (`weather_tool_server.py`).
    *   Maneja las entradas del usuario y muestra las respuestas.

2.  **`weather_tool_server.py`** - Este es el "proveedor de herramientas" que:
    *   Ofrece herramientas específicas relacionadas con el clima (`get_alerts`, `get_forecast`).
    *   Procesa las solicitudes de herramientas y devuelve los resultados.

3.  **MCP (Model-Client-Protocol)** - Este es el "sistema de comunicación" que:
    *   Proporciona formas estandarizadas para que los clientes descubran y llamen a las herramientas.
    *   Maneja la mensajería entre clientes y servidores.

### Flujo al Preguntar por el Clima

1.  **Entrada del Usuario**: Escribes una pregunta como "¿Cuál es el clima en Nueva York?" en el cliente.
2.  **Procesamiento del Cliente**:
    *   `mcp_gemini_client.py` envía esta pregunta a la IA de Gemini.
    *   También le dice a Gemini qué herramientas están disponibles consultando al servidor `weather_tool_server.py`.
3.  **Decisión de la IA de Gemini**:
    *   Gemini reconoce que necesita usar una herramienta meteorológica (por ejemplo, `get_forecast`).
    *   Formatea una respuesta indicando qué herramienta usar y con qué argumentos (por ejemplo, latitud y longitud para Nueva York).
4.  **Ejecución de la Herramienta**:
    *   El cliente analiza la solicitud de Gemini para usar la herramienta.
    *   Envía la solicitud de herramienta al servidor `weather_tool_server.py`.
    *   El servidor ejecuta la consulta meteorológica y devuelve los resultados.
5.  **Respuesta Final**:
    *   Los resultados de la herramienta regresan al cliente, que luego los envía de vuelta a Gemini.
    *   Gemini formatea estos resultados en una respuesta fácil de entender para el usuario.
    *   El cliente muestra esta respuesta final.

## Configuración y Ejecución

1.  **Instalar Dependencias**:
    ```bash
    pip install google-generativeai python-dotenv mcp-protocols # Asegúrate de que mcp-protocols sea el paquete correcto
    ```
2.  **Clave API**:
    *   Obtén una clave API de Google AI Studio.
    *   Crea un archivo `.env` en la raíz del proyecto.
    *   Añade tu clave al archivo `.env`:
        ```dotenv
        GEMINI_API_KEY=TU_CLAVE_API_AQUI
        ```
3.  **Ejecutar**:
    *   Asegúrate de que `mcp_gemini_client.py` y `weather_tool_server.py` estén en el mismo directorio.
    *   Ejecuta el cliente, diciéndole dónde encontrar el script del servidor:
        ```bash
        python mcp_gemini_client.py weather_tool_server.py
        ```
    *   Escribe tus consultas en la terminal cuando se te solicite.

## Archivo de Log (`mcp_log.txt`)

*   **Consolidado y Detallado:** Este archivo ahora contiene logs **combinados** tanto del cliente (`mcp_gemini_client.py`) como del servidor (`weather_tool_server.py`).
*   **Visibilidad del Flujo:** Los logs son intencionalmente **detallados** para mostrar el flujo de datos completo:
    *   Mensajes enviados/recibidos de la API de Gemini (incluyendo los prompts).
    *   Solicitudes/respuestas de herramientas enviadas/recibidas a través del protocolo MCP entre el cliente y el servidor.
*   **Identificación:** Cada entrada de log incluye el nombre del módulo (`mcp_gemini_client` o `weather_tool_server`) para que puedas identificar qué componente generó el mensaje.
*   **Depuración:** Es la fuente principal para depurar problemas y entender las interacciones entre todos los componentes.

### Flujo de Logs de Ejemplo (mcp_log.txt)

Aquí hay un ejemplo simplificado de cómo se ven los logs de una interacción completa, mostrando las comunicaciones clave:

1.  **Cliente envía el prompt inicial a Gemini (con descripción de herramientas):**
    ```log
    2025-04-21 12:31:54,519 - __main__ - INFO - === Prompt Sent to Gemini (Initial) ===
    You are an assistant that helps users with weather information.
    You have access to the following tools:
    ...
    Tool: get_forecast
    Description: Get weather forecast for a location...
    Schema: {...}
    ...
    When you need to use a tool, format your response like this:
    TOOL_NAME: {the tool name}
    TOOL_ARGS: {JSON formatted arguments for the tool}
    ...
    The user message is: cual es el tiempo en nyc ?
    ======================================
    ```

2.  **Gemini responde solicitando una herramienta:**
    ```log
    2025-04-21 12:31:56,049 - __main__ - INFO - === Raw Response Received from Gemini (Initial) ===
    TOOL_NAME: get_forecast
    TOOL_ARGS: {"latitude": 40.7128, "longitude": -74.0060}
    ===============================================
    ```

3.  **Cliente analiza la respuesta y envía la solicitud de herramienta MCP al servidor:**
    ```log
    2025-04-21 12:31:56,050 - __main__ - INFO - Executing MCP tool: get_forecast with args: {'latitude': 40.7128, 'longitude': -74.006}
    ```

4.  **Servidor recibe la solicitud de herramienta MCP:**
    ```log
    2025-04-21 12:31:56,052 - INFO - mcp.server.lowlevel.server - Processing request of type CallToolRequest
    2025-04-21 12:31:56,052 - INFO - __main__ - MCP Request Received: get_forecast with latitude: 40.7128, longitude: -74.006
    ```

5.  **Servidor ejecuta la herramienta y envía la respuesta MCP al cliente:**
    ```log
    2025-04-21 12:31:57,180 - INFO - __main__ - === MCP Response Sent (get_forecast) ===

                        Today:
                        Temperature: 56F
                        ...
                        Forecast: Cloudy. High near 56...
                        
    ---...
    =======================================
    ```

6.  **Cliente recibe la respuesta de la herramienta MCP:**
    ```log
    2025-04-21 12:31:57,182 - __main__ - INFO - Raw MCP Tool Result Object Received: meta=None content=[TextContent(type='text', text='\n                    Today:\n...)] isError=False
    2025-04-21 12:31:57,182 - __main__ - INFO - MCP tool get_forecast executed. Extracted Result Content: [TextContent(type='text', text='\n       Today:\n...)]...
    ```

7.  **Cliente envía el prompt final a Gemini (con resultado de la herramienta):**
    ```log
    2025-04-21 12:31:57,182 - __main__ - INFO - === Prompt Sent to Gemini (Final) ===
    I asked for information about the weather in response to: "cual es el tiempo en nyc ?"
                        
    I used the get_forecast tool with these arguments: {"latitude": 40.7128, "longitude": -74.006}
    The tool returned this result: [TextContent(type='text', text='\n     Today:\n...')]

    Please provide a helpful, user-friendly response based on this information.
    =======================================
    ```

8.  **Gemini responde con la respuesta final formateada para el usuario:**
    ```log
    2025-04-21 12:31:59,000 - __main__ - INFO - === Raw Response Received from Gemini (Final) ===
    The weather in NYC looks like this:

    **Today:** Cloudy with a high of 56F...
    ...
    ===============================================
    ```

---

# MCP Client Project with Gemini and Weather Tool Server

This repository demonstrates how to use the MCP (Model-Client-Protocol) to connect an AI client (using Google Gemini) with a server that provides specialized tools (in this case, weather tools).

## How it Works

The system acts as a bridge between the Gemini AI and specialized tools. Here's the flow explained simply:

### Component Roles

1.  **`mcp_gemini_client.py`** - This is the "middleman" that:
    *   Talks to the Gemini AI.
    *   Connects to the tool server (`weather_tool_server.py`).
    *   Handles user inputs and displays responses.

2.  **`weather_tool_server.py`** - This is the "tool provider" that:
    *   Offers specific weather-related tools (`get_alerts`, `get_forecast`).
    *   Processes tool requests and returns results.

3.  **MCP (Model-Client-Protocol)** - This is the "communication system" that:
    *   Provides standardized ways for clients to discover and call tools.
    *   Handles the messaging between clients and servers.

### Flow When Asking About Weather

1.  **User Input**: You type a question like "What's the weather in NYC?" into the client.
2.  **Client Processing**:
    *   `mcp_gemini_client.py` sends this question to the Gemini AI.
    *   It also tells Gemini what tools are available by checking with the `weather_tool_server.py` server.
3.  **Gemini AI's Decision**:
    *   Gemini recognizes it needs to use a weather tool (e.g., `get_forecast`).
    *   It formats a response indicating which tool to use and with what arguments (e.g., latitude and longitude for NYC).
4.  **Tool Execution**:
    *   The client parses Gemini's request to use the tool.
    *   It sends the tool request to the `weather_tool_server.py` server.
    *   The server runs the weather lookup and returns the results.
5.  **Final Response**:
    *   The tool results go back to the client, which then sends them back to Gemini.
    *   Gemini formats these results into a user-friendly answer.
    *   The client displays this final answer.

## Setup and Running

1.  **Install Dependencies**:
    ```bash
    pip install google-generativeai python-dotenv mcp-protocols # Ensure mcp-protocols is the correct package
    ```
2.  **API Key**:
    *   Get an API key from Google AI Studio.
    *   Create a `.env` file in the project root.
    *   Add your key to the `.env` file:
        ```dotenv
        GEMINI_API_KEY=YOUR_API_KEY_HERE
        ```
3.  **Run**:
    *   Ensure `mcp_gemini_client.py` and `weather_tool_server.py` are in the same directory.
    *   Run the client, telling it where to find the server script:
        ```bash
        python mcp_gemini_client.py weather_tool_server.py
        ```
    *   Type your queries in the terminal when prompted.

## Log File (`mcp_log.txt`)

*   **Consolidated & Verbose:** This single file now contains **combined** logs from both the client (`mcp_gemini_client.py`) and the server (`weather_tool_server.py`).
*   **Flow Visibility:** The logs are intentionally **verbose** to show the full data flow:
    *   Messages sent to/received from the Gemini API (including prompts).
    *   Tool requests/responses sent/received via the MCP protocol between the client and server.
*   **Identification:** Each log entry includes the module name (`mcp_gemini_client` or `weather_tool_server`) so you can identify which component generated the message.
*   **Debugging:** This is the primary source for debugging issues and understanding the interactions between all components.

### Example Log Flow (mcp_log.txt)

Here is a simplified example of what the logs look like for a full interaction, showing the key communications:

1.  **Client sends initial prompt to Gemini (with tool descriptions):**
    ```log
    2025-04-21 12:31:54,519 - __main__ - INFO - === Prompt Sent to Gemini (Initial) ===
    You are an assistant that helps users with weather information.
    You have access to the following tools:
    ...
    Tool: get_forecast
    Description: Get weather forecast for a location...
    Schema: {...}
    ...
    When you need to use a tool, format your response like this:
    TOOL_NAME: {the tool name}
    TOOL_ARGS: {JSON formatted arguments for the tool}
    ...
    The user message is: cual es el tiempo en nyc ?
    ======================================
    ```

2.  **Gemini responds requesting a tool:**
    ```log
    2025-04-21 12:31:56,049 - __main__ - INFO - === Raw Response Received from Gemini (Initial) ===
    TOOL_NAME: get_forecast
    TOOL_ARGS: {"latitude": 40.7128, "longitude": -74.0060}
    ===============================================
    ```

3.  **Client parses response and sends MCP tool request to server:**
    ```log
    2025-04-21 12:31:56,050 - __main__ - INFO - Executing MCP tool: get_forecast with args: {'latitude': 40.7128, 'longitude': -74.006}
    ```

4.  **Server receives MCP tool request:**
    ```log
    2025-04-21 12:31:56,052 - INFO - mcp.server.lowlevel.server - Processing request of type CallToolRequest
    2025-04-21 12:31:56,052 - INFO - __main__ - MCP Request Received: get_forecast with latitude: 40.7128, longitude: -74.006
    ```

5.  **Server runs tool and sends MCP response back to client:**
    ```log
    2025-04-21 12:31:57,180 - INFO - __main__ - === MCP Response Sent (get_forecast) ===

                        Today:
                        Temperature: 56F
                        ...
                        Forecast: Cloudy. High near 56...
                        
    ---...
    =======================================
    ```

6.  **Client receives MCP tool response:**
    ```log
    2025-04-21 12:31:57,182 - __main__ - INFO - Raw MCP Tool Result Object Received: meta=None content=[TextContent(type='text', text='\n                    Today:\n...)] isError=False
    2025-04-21 12:31:57,182 - __main__ - INFO - MCP tool get_forecast executed. Extracted Result Content: [TextContent(type='text', text='\n       Today:\n...)]...
    ```

7.  **Client sends final prompt to Gemini (with tool result):**
    ```log
    2025-04-21 12:31:57,182 - __main__ - INFO - === Prompt Sent to Gemini (Final) ===
    I asked for information about the weather in response to: "cual es el tiempo en nyc ?"
                        
    I used the get_forecast tool with these arguments: {"latitude": 40.7128, "longitude": -74.006}
    The tool returned this result: [TextContent(type='text', text='\n     Today:\n...')]

    Please provide a helpful, user-friendly response based on this information.
    =======================================
    ```

8.  **Gemini responds with the final user-friendly answer:**
    ```log
    2025-04-21 12:31:59,000 - __main__ - INFO - === Raw Response Received from Gemini (Final) ===
    The weather in NYC looks like this:

    **Today:** Cloudy with a high of 56F...
    ...
    ===============================================
    ```
