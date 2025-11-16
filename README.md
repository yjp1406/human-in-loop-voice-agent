# 🧠 Human-in-Loop Voice AI Agent
- A real-time, voice-enabled AI assistant built using LiveKit Agents, with supervisor escalation, bi-directional event messaging, and LLM-powered conversations.
  This system allows an AI agent to interact with users via voice, and automatically escalate to a human supervisor when needed. The supervisor can send replies back that the agent speaks aloud in the call.

# 🚀 Features
# 🎤 Real-time Voice AI
- Deepgram Nova-3 STT
- OpenAI GPT-4.1 mini LLM
- ElevenLabs Turbo TTS
- Silero VAD + Multilingual turn detection

# 🧑‍💼 Human-in-Loop (Escalation)
- Agent triggers a transfer_to_human tool
- Supervisor dashboard receives the question
- Human types a reply
- AI agent receives that reply via LiveKit data packets
- Agent speaks the reply to the caller

# 🔄 Two-way Data Messaging

- Backend → Supervisor (updates, questions)
- Supervisor → Backend/Agent (reply)
- Frontend subscribed using livekit-js
- Reliable message delivery

# 🔐 Secure Token Generation
- Server-side access tokens
- JWT with room-join and data publish permissions
- Compatible with LiveKit Cloud

# 🔧 Requirements
# Python packages
- livekit-agents
- livekit
- python-dotenv
- openai
- deepgram-sdk
- elevenlabs
- aiohttp

# ⚙️ Environment Setup (.env.local)
- LIVEKIT_URL=wss://<your-livekit>.livekit.cloud
- LIVEKIT_API_KEY=<key>
- LIVEKIT_API_SECRET=<secret>



