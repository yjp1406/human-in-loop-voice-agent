from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from prompt import AGENT_INSTRUCTIONS, SESSION_INSTRUCTIONS
from tool import transfer_to_human, supervisor_respond
import json, asyncio

load_dotenv(".env.local")

class Assistant(Agent):
    def __init__(self):
        super().__init__(
            instructions=AGENT_INSTRUCTIONS,
            tools=[transfer_to_human, supervisor_respond],
        )

async def entrypoint(ctx: agents.JobContext):
    print("joined room:", ctx.room.name)
    session = AgentSession(
        stt="deepgram/nova-3:en",
        llm="openai/gpt-4.1-mini",
        tts="elevenlabs/eleven_turbo_v2:iP95p4xoKVk53GoZ742B",
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    assistant = Assistant()
    lk_room = await session.start(
        room=ctx.room,
        agent=assistant,
        room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC()),
    )

    print("✅ Agent joined LiveKit room successfully.")
    room = ctx.room
    print("Current room: ", room.name)
    # print("room token: ", ctx.room.token)

    @ctx.room.on("data_packet_received")
    def on_data_received(participant, data, kind):
        try:
            msg = json.loads(data.decode("utf-8"))
            print("📩 Received:", msg.get("answer"))
            if msg.get("type") == "supervisor_reply":
                reply = msg.get("answer", "")
                asyncio.create_task(
                    session.output_stream.send_text(f"The supervisor replied: {reply}")
                )
        except Exception as e:
            print(f"❌ Error handling message: {e}")



    async def handle_data(participant, data, kind):
        try:
            msg = json.loads(data.decode("utf-8"))

            if msg.get("type") == "supervisor_reply":
                reply = msg.get("answer", "")
                await session.output_stream.send_text(
                    f"The supervisor replied: {reply}"
                )

        except Exception as e:
            print(f"❌ Error handling message: {e}")

    await session.generate_reply(instructions=SESSION_INSTRUCTIONS)

    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
