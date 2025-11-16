console.log("✅ main.js loaded!");
import * as Livekit from "https://cdn.jsdelivr.net/npm/livekit-client/+esm";

const LIVEKIT_URL = "wss://aifrontdesk-c1sgp5bp.livekit.cloud"; 
let room;

async function loadData() {
  const res = await fetch("/api/data");
  const data = await res.json();

  document.getElementById("pending").innerHTML =
    data.pending
      .map((r) => `<div><b>${r.id}</b>: ${r.question}</div>`)
      .join("") || "None";

  document.getElementById("history").innerHTML =
    data.history
      .map(
        (r) =>
          `<div>${r.status.toUpperCase()} - ${r.question} → ${
            r.answer || "—"
          }</div>`
      )
      .join("") || "None";

  document.getElementById("kb").innerHTML =
    data.knowledge
      .map((k) => `<div><b>${k.topic_key}</b>: ${k.answer}</div>`)
      .join("") || "None";
}

async function sendResponse(e) {
  e.preventDefault();
  const fd = new FormData();
  fd.append("request_id", document.getElementById("req-id").value);
  fd.append("answer", document.getElementById("answer").value);

  const res = await fetch("/api/respond", { method: "POST", body: fd });
  console.log("📤 Sent response, server replied with:", res);

  document.getElementById("req-id").value = "";
  document.getElementById("answer").value = "";

  await loadData();
}

// --- Simulate AI escalation (for testing) ---
async function simulateTransfer(e) {
  e.preventDefault();
  const fd = new FormData();
  fd.append("customer_id", document.getElementById("cust-id").value);
  fd.append("question", document.getElementById("question").value);
  await fetch("/api/transfer", { method: "POST", body: fd });
  await loadData();
}

// --- Real-time LiveKit listener ---
// --- Real-time LiveKit listener ---
async function connectLiveKit() {
  try {
    const res = await fetch("/api/token?identity=test_user");
    const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoidGVzdF91c2VyIiwidmlkZW8iOnsicm9vbUpvaW4iOnRydWUsInJvb20iOiJzdXBlcnZpc29yX3Jvb20iLCJjYW5QdWJsaXNoIjp0cnVlLCJjYW5TdWJzY3JpYmUiOnRydWUsImNhblB1Ymxpc2hEYXRhIjp0cnVlfSwic3ViIjoidGVzdF91c2VyIiwiaXNzIjoiQVBJYmROQmZiRDdmVVV4IiwibmJmIjoxNzYzMjgyMzg5LCJleHAiOjE3NjMzMDM5ODl9.TdS_DfBg4ghwcsx_rPRasYeB7diHCgSD02NNh4RKzus"
    console.log("🔑 Obtained LiveKit token for room:", token);

    room = new Livekit.Room();

    const result = await room.connect(LIVEKIT_URL, token);
    console.log(" result ", result);

    console.log("✅ Connected to LiveKit room:", "supervisor_room");

    room.on(Livekit.RoomEvent.DataReceived, (payload, participant) => {
      try {
        const msg = JSON.parse(new TextDecoder().decode(payload));
        console.log("📩 Received:", msg);

        if (msg.type === "supervisor_reply" || msg.type === "transfer_update") {
          loadData();
        }
      } catch (err) {
        console.error("Failed to parse LiveKit message:", err);
      }
    });

  } catch (err) {
    console.error("❌ LiveKit connection failed:", err);
  }
}

window.onload = async () => {
  console.log("🚀 Window loaded — initializing dashboard...");
  await loadData();
  await connectLiveKit();
};

window.sendResponse = sendResponse;
window.simulateTransfer = simulateTransfer;
