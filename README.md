AI Agent with OpenAI and Twilio WhatsApp Integration

Project Overview - 
This project develops an AI agent using the OpenAI API that integrates with Twilio's WhatsApp functionality. The AI agent accepts the users return orders and update them in database.

Features

    Real-time user interactions via WhatsApp.
    AI agent developed using OpenAI's gpt-4.0-mini model.
    Accepts return orders requests and update them in database.
    FastAPI: Backend framework for handling API requests and integrating OpenAI with Twilio.
    OpenAI API: Powers the AI agent for generating intelligent responses.
    Twilio API: Handles WhatsApp messaging functionality.
    Python: Core programming language for the entire project.

Clone the repository: git clone https://github.com/namanbhardwaj19/Drape_bot

Install the required dependencies: pip install -r requirements.txt

Set up the Twilio API:

-Create a Twilio account.

-Get your Twilio WhatsApp sandbox number.

-Configure your conversation service webhook to point to your FastAPI app endpoint.

Set up OpenAI API:

-Create an OpenAI account.

-Get your OpenAI API key from the OpenAI platform.

-Set your API key in your environment variables or directly in the code.

Run the FastAPI server:

    uvicorn main:app --reload

OR

    just run run.py

Expose your local development server using ngrok for Twilio to access your webhook:

-Install ngrok

-Set auth token in ngrok config

-RUN ngrok http 8000

Configuration: Add your OpenAI API key and Twilio credentials in the project’s .env file or as environment variables.

Usage:

-Once the server is up and running, users can interact with the AI agent via WhatsApp.

-The agent will be handling the return order requests like - I am returning 10 meters of red drape.

CODE STRUCTURE

    Main Application (main.py): This is the entry point of the FastAPI server. It creates the app and routes the incoming requests from Twilio to /whatsapp endpoint. Run run.py to start the server

    API Handlers: The src/init.py file has /whatsapp endpoint to receives WhatsApp messages. This function processes the user's message, sends it to the OpenAI API.

    OpenAI Integration: The /whatsapp endpoint sends the user message to the OpenAI API to generate a response using the provided prompt. The response is then formatted and sent back to the FastAPI handler. OpenAI suggests to call the function if it is a return request. Then the actual function will be called and update the returned item in database.
