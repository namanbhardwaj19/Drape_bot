import mimetypes
import os
import psycopg2
import json
import requests
from fastapi.logger import logger
from openai import OpenAI
from twilio.rest import Client
from fastapi import Request, APIRouter
from requests.exceptions import Timeout
from src.prompts import system_prompt

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
DB_CONNECTION_URL = os.environ.get("DB_CONNECTION_URL")
OPEN_AI_API_KEY = os.environ.get("OPEN_AI_API_KEY")


drape = APIRouter(
    prefix="/v1"
)


function_definitions = [
    {
        "name": "update_drape_stock",
        "description": "Updates the stock of drapes in the database when a user is returning it.",
        "parameters": {
            "type": "object",
            "properties": {
                "item": {"type": "string", "description": "Item name"},
                "size": {"type": "number", "description": "Size of the drape"},
                "color": {"type": "string", "description": "Color of the drape"},
                "status": {"type": "string", "description": "Status of the order"}
            },
            "required": ["item", "size", "color", "status"]
        }
    }
]

client = OpenAI(
    api_key=OPEN_AI_API_KEY,
)
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def process_message(user_message, user_phone):
    conversation_history = {"role": "user", "content": user_message}
    # Send the user message to OpenAI with function definitions
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[system_prompt, conversation_history],
        functions=function_definitions,
        function_call="auto"
    )

    response = response.dict()
    # Extract function call details if available
    function_call = response.get('choices', [{}])[0].get('message', {}).get('function_call')

    if function_call:
        function_name = function_call['name']
        function_args = json.loads(function_call['arguments'])

        # Handle the specific function call
        if function_name == "update_drape_stock":
            update_drape_stock(
                item=function_args["item"],
                color=function_args['color'],
                size=function_args['size'],
                status=function_args['status'],
                returned_by=user_phone
            )
        assistant_message = "Item has been successfully returned and updated in the database"
    else:
        assistant_message = response['choices'][0]['message'].get('content')
    # If no function call, return the assistant's response as text
    return assistant_message


def update_drape_stock(item: str, color: str, size: float, status: str, returned_by: str):
    conn = psycopg2.connect(DB_CONNECTION_URL)
    cur = conn.cursor()
    insert_query = """
    INSERT INTO drapes_return_status (item, color, size, status, returned_by)
    VALUES (%s, %s, %s, %s, %s);
    """
    cur.execute(insert_query, (item, color, size, status, returned_by))
    conn.commit()
    cur.close()
    conn.close()
    return True


@drape.post('/whatsapp')
async def whatsapp_endpoint(request: Request):
    """
    :param request: Request object from Twilio
    :return: Message acknowledgement with status 200
    """
    try:
        form_data = await request.form()

        # Extract relevant Twilio fields
        user_phone_number = form_data.get("From")
        user_phone = user_phone_number.split(":")[-1]
        message_body = form_data.get("Body")  # For text messages
        media_url = form_data.get("MediaUrl0")  # For media (voice recordings)
        media_content_type = form_data.get("MediaContentType0")  # Content type (e.g., audio/ogg)

        if message_body:
            # Handle text message
            response = process_message(message_body, user_phone)

        elif media_url and media_content_type.startswith("audio/"):
            # Handle voice message (requires transcription)
            transcription = transcribe_audio(media_url)
            if transcription:
                response = process_message(transcription, user_phone)
            else:
                response = "Could not transcribe voice message."

        else:
            response = "Unsupported message type"

        twilio_client.messages.create(body=response, from_='whatsapp:+14155238886', to=user_phone_number)
        # Create Twilio WhatsApp response

    except Exception as e:
        logger.error(f"Got an exception - {e}")


def transcribe_audio(media_url):
    auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    try:
        response = requests.get(media_url, auth=auth, timeout=10)
        response.raise_for_status()
    except Timeout:
        return None
    except Exception as e:
        logger.exception(f"Error while transcribing audio {e}")

    content_type = response.headers['Content-Type']
    ext = mimetypes.guess_extension(content_type)
    if ext not in ['.flac', '.m4a', '.mp3', '.mp4', '.mpeg', '.mpga', '.oga', '.ogg', '.wav', '.webm']:
        return None

    temp_audio_file = f"temp_audio{ext}"
    with open(temp_audio_file, 'wb') as f:
        f.write(response.content)

    with open(temp_audio_file, 'rb') as f:
        response = client.audio.transcriptions.create(model="whisper-1",
                                                      file=f)
        return response.text


def db_connect():
    conn = psycopg2.connect(DB_CONNECTION_URL)
    cur = conn.cursor()
    return cur