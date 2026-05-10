/**
 * SwiftShip Voice Support – Realtime API Client
 *
 * Connects to Azure OpenAI Realtime API via WebSocket, streams audio
 * bidirectionally, and handles tool/function calls for order lookup,
 * policy search, and ticket creation.
 */

// ── DOM refs ────────────────────────────────────────────────
const connectBtn = document.getElementById("connect-btn");
const micBtn = document.getElementById("mic-btn");
const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");
const transcript = document.getElementById("transcript");
const endpointInput = document.getElementById("endpoint");
const deploymentInput = document.getElementById("deployment");
const apiKeyInput = document.getElementById("api-key");

// ── State ───────────────────────────────────────────────────
let ws = null;
let micStream = null;
let audioContext = null;
let sourceNode = null;
let processorNode = null;
let playbackCtx = null;
let isRecording = false;
let reconnectAttempts = 0;
const MAX_RECONNECT = 3;

// ── System prompt (mirrors docs/agent-instructions.md) ──────
const SYSTEM_INSTRUCTIONS = `You are SwiftShip's friendly voice support agent. You help customers with order tracking, returns, refunds, cancellations, and general logistics questions.

Guidelines:
- Keep every response to 2–3 sentences maximum — you are on a voice call.
- Be warm, empathetic, and professional.
- When the customer provides an order ID, call lookup_order immediately.
- For policy questions (refunds, damage claims, cancellations), call search_policies.
- If the issue cannot be resolved automatically, offer to create a support ticket with create_ticket.
- Spell out IDs slowly (e.g., "O-R-D, one-two-three-four").
- Never expose raw JSON or technical details to the customer.`;

// ── Tool definitions ────────────────────────────────────────
const TOOLS = [
  {
    type: "function",
    name: "lookup_order",
    description:
      "Look up a customer order by its order ID. Returns order status, items, shipping info, and estimated delivery.",
    parameters: {
      type: "object",
      properties: {
        order_id: {
          type: "string",
          description: "The order ID, e.g. ORD-1234",
        },
      },
      required: ["order_id"],
    },
  },
  {
    type: "function",
    name: "search_policies",
    description:
      "Search SwiftShip support policies using a natural-language query. Returns the most relevant policy document sections.",
    parameters: {
      type: "object",
      properties: {
        query: {
          type: "string",
          description:
            "Natural language query, e.g. 'What is the refund policy for damaged items?'",
        },
      },
      required: ["query"],
    },
  },
  {
    type: "function",
    name: "create_ticket",
    description:
      "Create a support ticket for issues that need human follow-up.",
    parameters: {
      type: "object",
      properties: {
        order_id: { type: "string", description: "Related order ID" },
        customer_name: { type: "string", description: "Customer full name" },
        issue_type: {
          type: "string",
          enum: [
            "damaged_item",
            "cancellation",
            "refund",
            "lost_package",
            "general",
          ],
        },
        description: {
          type: "string",
          description: "Brief description of the issue",
        },
        priority: { type: "string", enum: ["high", "medium", "low"] },
      },
      required: ["order_id", "customer_name", "issue_type", "description"],
    },
  },
];

// ── Connect / Disconnect ────────────────────────────────────
connectBtn.addEventListener("click", () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    disconnect();
  } else {
    connect();
  }
});

function connect() {
  const endpoint = endpointInput.value.trim().replace(/^https?:\/\//, "");
  const deployment = deploymentInput.value.trim();
  const apiKey = apiKeyInput.value.trim();

  if (!endpoint || !deployment || !apiKey) {
    alert("Please fill in all connection fields.");
    return;
  }

  const url = `wss://${endpoint}/openai/realtime?api-version=2025-04-01-preview&deployment=${deployment}&api-key=${apiKey}`;

  setStatus("thinking", "Connecting…");
  connectBtn.disabled = true;

  ws = new WebSocket(url);

  ws.addEventListener("open", onOpen);
  ws.addEventListener("message", onMessage);
  ws.addEventListener("error", onError);
  ws.addEventListener("close", onClose);
}

function disconnect() {
  if (ws) {
    ws.close();
    ws = null;
  }
  stopMic();
  setStatus("idle", "Disconnected");
  connectBtn.textContent = "Connect";
  connectBtn.classList.remove("connected");
  micBtn.disabled = true;
}

// ── WebSocket handlers ──────────────────────────────────────
function onOpen() {
  reconnectAttempts = 0;
  setStatus("idle", "Connected");
  connectBtn.textContent = "Disconnect";
  connectBtn.classList.add("connected");
  connectBtn.disabled = false;
  micBtn.disabled = false;
  addSystemMessage("Connected to Azure OpenAI Realtime API.");

  // Send session configuration
  send("session.update", {
    session: {
      voice: "alloy",
      instructions: SYSTEM_INSTRUCTIONS,
      tools: TOOLS,
      turn_detection: { type: "server_vad" },
      input_audio_transcription: { model: "whisper-1" },
    },
  });
}

function onMessage(event) {
  let data;
  try {
    data = JSON.parse(event.data);
  } catch {
    return;
  }

  switch (data.type) {
    // Session lifecycle
    case "session.created":
    case "session.updated":
      console.log(`[session] ${data.type}`);
      break;

    // Input transcript (user speech)
    case "conversation.item.input_audio_transcription.completed":
      if (data.transcript) {
        addMessage("user", data.transcript);
      }
      break;

    // Agent response text
    case "response.audio_transcript.delta":
      appendAgentDelta(data.delta);
      break;

    case "response.audio_transcript.done":
      finalizeAgentMessage();
      break;

    // Agent audio playback
    case "response.audio.delta":
      playAudioDelta(data.delta);
      break;

    // Status changes
    case "input_audio_buffer.speech_started":
      setStatus("listening", "Listening…");
      break;

    case "input_audio_buffer.speech_stopped":
      setStatus("thinking", "Processing…");
      break;

    case "response.created":
      setStatus("thinking", "Thinking…");
      break;

    case "response.audio.done":
      setStatus("idle", "Ready");
      break;

    // Function / tool calls
    case "response.function_call_arguments.done":
      handleFunctionCall(data);
      break;

    case "error":
      console.error("[error]", data.error);
      addSystemMessage(`Error: ${data.error?.message || "Unknown error"}`);
      break;

    default:
      // Ignore other event types
      break;
  }
}

function onError(err) {
  console.error("[ws error]", err);
  setStatus("idle", "Connection error");
  connectBtn.disabled = false;
}

function onClose(event) {
  console.log("[ws close]", event.code, event.reason);
  stopMic();
  micBtn.disabled = true;

  if (event.code !== 1000 && reconnectAttempts < MAX_RECONNECT) {
    reconnectAttempts++;
    const delay = reconnectAttempts * 2000;
    addSystemMessage(
      `Connection lost. Reconnecting in ${delay / 1000}s… (attempt ${reconnectAttempts}/${MAX_RECONNECT})`
    );
    setStatus("thinking", "Reconnecting…");
    setTimeout(connect, delay);
  } else {
    setStatus("idle", "Disconnected");
    connectBtn.textContent = "Connect";
    connectBtn.classList.remove("connected");
    connectBtn.disabled = false;
  }
}

// ── Send helper ─────────────────────────────────────────────
function send(type, payload = {}) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type, ...payload }));
  }
}

// ── Microphone ──────────────────────────────────────────────
micBtn.addEventListener("click", toggleMic);

async function toggleMic() {
  if (isRecording) {
    stopMic();
  } else {
    await startMic();
  }
}

async function startMic() {
  try {
    micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioContext = new AudioContext({ sampleRate: 24000 });
    sourceNode = audioContext.createMediaStreamSource(micStream);

    // Use ScriptProcessor for broad compatibility (AudioWorklet preferred in prod)
    processorNode = audioContext.createScriptProcessor(4096, 1, 1);
    processorNode.onaudioprocess = (e) => {
      if (!isRecording) return;
      const float32 = e.inputBuffer.getChannelData(0);
      const int16 = float32ToInt16(float32);
      const base64 = arrayBufferToBase64(int16.buffer);
      send("input_audio_buffer.append", { audio: base64 });
    };

    sourceNode.connect(processorNode);
    processorNode.connect(audioContext.destination);

    isRecording = true;
    micBtn.classList.add("active");
    setStatus("listening", "Listening…");
  } catch (err) {
    console.error("Mic error:", err);
    addSystemMessage("Could not access microphone. Check permissions.");
  }
}

function stopMic() {
  isRecording = false;
  micBtn.classList.remove("active");

  if (processorNode) {
    processorNode.disconnect();
    processorNode = null;
  }
  if (sourceNode) {
    sourceNode.disconnect();
    sourceNode = null;
  }
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
  if (micStream) {
    micStream.getTracks().forEach((t) => t.stop());
    micStream = null;
  }
}

// ── Audio Playback ──────────────────────────────────────────
function playAudioDelta(base64) {
  if (!base64) return;
  setStatus("speaking", "Speaking…");

  if (!playbackCtx) {
    playbackCtx = new AudioContext({ sampleRate: 24000 });
  }

  const raw = atob(base64);
  const bytes = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);

  const int16 = new Int16Array(bytes.buffer);
  const float32 = new Float32Array(int16.length);
  for (let i = 0; i < int16.length; i++) float32[i] = int16[i] / 32768;

  const buffer = playbackCtx.createBuffer(1, float32.length, 24000);
  buffer.getChannelData(0).set(float32);

  const src = playbackCtx.createBufferSource();
  src.buffer = buffer;
  src.connect(playbackCtx.destination);
  src.start();
}

// ── Function Call Handling ──────────────────────────────────
async function handleFunctionCall(data) {
  const { call_id, name, arguments: argsJson } = data;
  let args;
  try {
    args = JSON.parse(argsJson);
  } catch {
    args = {};
  }

  addSystemMessage(`Calling tool: ${name}`);
  console.log(`[tool] ${name}`, args);

  let result;
  switch (name) {
    case "lookup_order":
      result = await mockLookupOrder(args.order_id);
      break;
    case "search_policies":
      result = await mockSearchPolicies(args.query);
      break;
    case "create_ticket":
      result = await mockCreateTicket(args);
      break;
    default:
      result = { error: `Unknown tool: ${name}` };
  }

  // Return result to the model
  send("conversation.item.create", {
    item: {
      type: "function_call_output",
      call_id,
      output: JSON.stringify(result),
    },
  });

  // Ask the model to continue generating a response
  send("response.create");
}

// ── Mock Tool Implementations ───────────────────────────────
async function mockLookupOrder(orderId) {
  return {
    order_id: orderId,
    status: "in_transit",
    items: [
      { name: "Wireless Headphones", quantity: 1, price: 79.99 },
      { name: "Phone Case", quantity: 2, price: 15.99 },
    ],
    shipping: {
      carrier: "SwiftShip Express",
      tracking_number: "SSX-998877",
      estimated_delivery: "2025-07-20",
      current_location: "Denver Distribution Center",
    },
    customer_name: "Alex Johnson",
    order_date: "2025-07-14",
  };
}

async function mockSearchPolicies(query) {
  return {
    results: [
      {
        title: "Refund & Return Policy",
        content:
          "Customers may request a full refund within 30 days of delivery for undamaged items. Damaged items are eligible for immediate replacement or refund. Refunds are processed within 5–7 business days after the returned item is received.",
        relevance_score: 0.94,
      },
      {
        title: "Order Cancellation Policy",
        content:
          "Orders can be cancelled free of charge if they have not yet been shipped. Once an order is in transit, customers may refuse delivery for a full refund or initiate a return after delivery.",
        relevance_score: 0.87,
      },
    ],
    query,
  };
}

async function mockCreateTicket(args) {
  const ticketId = `TKT-${Date.now().toString().slice(-6)}`;
  return {
    ticket_id: ticketId,
    status: "open",
    created_at: new Date().toISOString(),
    order_id: args.order_id,
    customer_name: args.customer_name,
    issue_type: args.issue_type,
    description: args.description,
    priority: args.priority || "medium",
  };
}

// ── Transcript UI ───────────────────────────────────────────
let currentAgentMsg = null;

function addMessage(role, text) {
  removePlaceholder();
  const el = document.createElement("div");
  el.className = `message ${role}`;
  el.textContent = text;
  transcript.appendChild(el);
  transcript.scrollTop = transcript.scrollHeight;
}

function addSystemMessage(text) {
  removePlaceholder();
  const el = document.createElement("div");
  el.className = "message system";
  el.textContent = text;
  transcript.appendChild(el);
  transcript.scrollTop = transcript.scrollHeight;
}

function appendAgentDelta(delta) {
  if (!delta) return;
  removePlaceholder();
  if (!currentAgentMsg) {
    currentAgentMsg = document.createElement("div");
    currentAgentMsg.className = "message agent";
    transcript.appendChild(currentAgentMsg);
  }
  currentAgentMsg.textContent += delta;
  transcript.scrollTop = transcript.scrollHeight;
}

function finalizeAgentMessage() {
  currentAgentMsg = null;
}

function removePlaceholder() {
  const ph = transcript.querySelector(".transcript-placeholder");
  if (ph) ph.remove();
}

// ── Status helper ───────────────────────────────────────────
function setStatus(state, text) {
  statusDot.className = `status-dot ${state}`;
  statusText.textContent = text;
}

// ── Audio utils ─────────────────────────────────────────────
function float32ToInt16(float32) {
  const int16 = new Int16Array(float32.length);
  for (let i = 0; i < float32.length; i++) {
    const s = Math.max(-1, Math.min(1, float32[i]));
    int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return int16;
}

function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
}
