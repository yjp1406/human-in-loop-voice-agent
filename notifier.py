import os, json, asyncio

from numpy import identity
from livekit import api
from dotenv import load_dotenv
from livekit.api import room_service as rs
from livekit import rtc

load_dotenv(".env.local")

async def notify_agent_of_supervisor_reply(request_id: str, answer: str):
    """
    Sends a DataChannel message to the AI agent in the LiveKit room
    using the LiveKit Server API. This is the ONLY method that
    LiveKit Agents receive as `data_received` events.
    """
    LIVEKIT_URL = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")


    room_name = "supervisor_room"  
    token = await generate_livekit_token(room_name, "event_sender")

    payload = {
        "type": "supervisor_reply",
        "request_id": request_id,
        "answer": answer
    }
    room = rtc.Room()
    try:
        await room.connect("wss://aifrontdesk-c1sgp5bp.livekit.cloud", token) 
        print(f"Connected to room: {room_name}")

        data_bytes = json.dumps(payload).encode("utf-8") 
  

        await room.local_participant.publish_data(
            data_bytes,
            reliable=True
        )
        print(f"Event sent to room '{room_name}': {payload}")

    except Exception as e:
        print(f"Error connecting to or sending event in room '{room_name}': {e}")
    finally:
        # 4. Disconnect from the room when done
        # await room.disconnect()
        print(f"Disconnected from room: {room_name}")

async def generate_livekit_token(room_name: str, participant_identity: str) -> str:
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    token = api.AccessToken(api_key, api_secret) \
        .with_identity(participant_identity) \
        .with_name("event_sender") \
        .with_grants(api.VideoGrants(
            room_join=True,
            room="supervisor_room",
            can_publish=True,
            can_subscribe=True
        ))
    return token.to_jwt()


async def send_event_to_room(room_name: str, payload: dict):
    token = await generate_livekit_token(room_name, "event_sender")
    print(f"Generated token for room '{room_name}': {token}")

    room = rtc.Room()
    try:
        await room.connect("wss://aifrontdesk-c1sgp5bp.livekit.cloud", token) 
        print(f"Connected to room: {room_name}")

        data_bytes = json.dumps(payload).encode("utf-8") 
        await room.local_participant.publish_data(
            data_bytes,
            reliable=True
        )
        print(f"Event sent to room '{room_name}': {payload}")

    except Exception as e:
        print(f"Error connecting to or sending event in room '{room_name}': {e}")
    finally:
        # await room.disconnect()
        print(f"Disconnected from room: {room_name}")