/**
 * Micro-Bridge WhatsApp QR Code (Baileys) -> Painel de Busca FastAPI
 *
 * Implementa o mesmo contrato HTTP da skill `agente-barbearia` (UAZAPI):
 * - GET  /status            -> { connected, status, phone, qr_data_url }
 * - POST /send/text         -> { number, text, linkPreview }
 * - POST /message/markread  -> { id: string[] }
 * - POST /message/presence  -> { number, presence: 'composing' | 'paused' }
 *
 * E encaminha todas as mensagens recebidas/enviadas para:
 *   POST http://127.0.0.1:8090/api/agent/webhook
 * preservando `fromMe`, `wasSentByApi`, `chatid` (nunca @lid) e `messageid`.
 */

const express = require("express");
const path = require("path");
const pino = require("pino");
const QRCode = require("qrcode");
const qrcodeTerminal = require("qrcode-terminal");
const {
  default: makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
} = require("@whiskeysockets/baileys");

// Suprime ruído interno do libsignal referente a mensagens antigas de sincronização (Bad MAC)
const origConsoleError = console.error;
console.error = function (...args) {
  const msg = String(args[0] || "");
  if (
    msg.includes("Failed to decrypt message with any known session") ||
    msg.includes("Bad MAC") ||
    msg.includes("Session error:")
  ) {
    return;
  }
  origConsoleError.apply(console, args);
};

const PORT = Number(process.env.BRIDGE_PORT || 3100);
const FASTAPI_WEBHOOK_URL =
  process.env.FASTAPI_WEBHOOK_URL || "http://127.0.0.1:8090/api/agent/webhook";
const AUTH_DIR = path.join(__dirname, "auth_info");

const app = express();
app.use(express.json({ limit: "2mb" }));

let sock = null;
let connectionStatus = "initializing";
let qrDataUrl = null;
let connectedPhone = null;

// Guarda IDs enviados via API (/send/text) para diferenciar de mensagens digitadas manualmente pelo humano no celular
const sentByApiIds = new Set();

function digitsOnly(val) {
  return String(val || "")
    .split("@")[0]
    .split(":")[0]
    .replace(/\D/g, "");
}

function toWhatsappJid(number) {
  const d = digitsOnly(number);
  if (!d) throw new Error(`Numero invalido: ${number}`);
  return `${d}@s.whatsapp.net`;
}

async function forwardToFastApi(payload) {
  try {
    await fetch(FASTAPI_WEBHOOK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (err) {
    console.warn("[bridge] Aviso ao notificar FastAPI:", err.message || err);
  }
}

async function startWhatsApp() {
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
  let version = [2, 3000, 1015901307];
  try {
    const latest = await fetchLatestBaileysVersion();
    if (latest && latest.version) version = latest.version;
  } catch (_) {}

  sock = makeWASocket({
    version,
    auth: state,
    logger: pino({ level: "silent" }),
    printQRInTerminal: false,
    browser: ["Painel de Busca", "Chrome", "1.0.0"],
    syncFullHistory: false,
    shouldSyncHistoryMessage: () => false,
    shouldIgnoreJid: (jid) =>
      !jid ||
      jid.endsWith("@broadcast") ||
      jid.endsWith("@newsletter") ||
      jid === "status@broadcast",
    getMessage: async () => undefined,
  });

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", async (update) => {
    const { connection, lastDisconnect, qr } = update;
    if (qr) {
      connectionStatus = "qr_ready";
      qrDataUrl = await QRCode.toDataURL(qr);
      console.log("\n[bridge] Escaneie o QR Code abaixo ou direto na tela do Painel de Busca:");
      qrcodeTerminal.generate(qr, { small: true });
    }
    if (connection === "open") {
      connectionStatus = "connected";
      qrDataUrl = null;
      connectedPhone = digitsOnly(sock.user && sock.user.id);
      console.log(`[bridge] WhatsApp conectado com sucesso: ${connectedPhone}`);
    } else if (connection === "close") {
      const code =
        lastDisconnect &&
        lastDisconnect.error &&
        lastDisconnect.error.output &&
        lastDisconnect.error.output.statusCode;
      const shouldReconnect = code !== DisconnectReason.loggedOut;
      connectionStatus = shouldReconnect ? "reconnecting" : "logged_out";
      qrDataUrl = null;
      if (code === 515) {
        console.log("[bridge] Sincronização pós-pareamento concluída (code 515), reconectando socket...");
        setTimeout(startWhatsApp, 1500);
      } else {
        console.warn(`[bridge] Conexao encerrada (code=${code}). Reconectar=${shouldReconnect}`);
        if (shouldReconnect) {
          setTimeout(startWhatsApp, 3000);
        }
      }
    }
  });

  sock.ev.on("messages.upsert", async ({ messages, type }) => {
    if (type !== "notify") return;
    for (const m of messages || []) {
      const remoteJid = (m.key && m.key.remoteJid) || "";
      if (!remoteJid || remoteJid.endsWith("@g.us") || remoteJid === "status@broadcast") {
        continue;
      }
      // Cicatriz #1: Nunca repassar @lid como chatid se houver remoteJid telefonico
      if (remoteJid.endsWith("@lid")) continue;

      const msgId = (m.key && m.key.id) || "";
      const fromMe = Boolean(m.key && m.key.fromMe);
      const wasSentByApi = sentByApiIds.has(msgId);
      if (wasSentByApi) {
        sentByApiIds.delete(msgId);
      }

      const text =
        (m.message && m.message.conversation) ||
        (m.message && m.message.extendedTextMessage && m.message.extendedTextMessage.text) ||
        "";

      if (!text && !fromMe) continue;

      await forwardToFastApi({
        EventType: "messages",
        instanceName: "painel-qr-bridge",
        message: {
          fromMe,
          isGroup: remoteJid.endsWith("@g.us"),
          wasSentByApi,
          type: text ? "text" : "other",
          text: text || "",
          chatid: remoteJid,
          senderName: m.pushName || "",
          messageid: msgId,
        },
      });
    }
  });
}

app.get("/status", (_req, res) => {
  res.json({
    connected: connectionStatus === "connected",
    status: connectionStatus,
    phone: connectedPhone,
    qr_data_url: qrDataUrl,
  });
});

app.post("/send/text", async (req, res) => {
  try {
    if (!sock || connectionStatus !== "connected") {
      return res.status(503).json({ error: "WhatsApp ainda nao conectado via QR Code" });
    }
    const { number, text } = req.body || {};
    const jid = toWhatsappJid(number);
    const sent = await sock.sendMessage(jid, { text: String(text || "") });
    const msgId = (sent && sent.key && sent.key.id) || "";
    if (msgId) {
      sentByApiIds.add(msgId);
      setTimeout(() => sentByApiIds.delete(msgId), 60000);
    }
    return res.json({ ok: true, messageid: msgId });
  } catch (err) {
    return res.status(500).json({ error: String(err.message || err) });
  }
});

app.post("/message/presence", async (req, res) => {
  try {
    if (sock && connectionStatus === "connected") {
      const { number, presence } = req.body || {};
      const jid = toWhatsappJid(number);
      await sock.sendPresenceUpdate(presence === "composing" ? "composing" : "paused", jid);
    }
  } catch (_) {}
  res.json({ ok: true });
});

app.post("/message/markread", async (_req, res) => {
  res.json({ ok: true });
});

app.listen(PORT, () => {
  console.log(`[bridge] Micro-bridge WhatsApp QR Code ouvindo em http://127.0.0.1:${PORT}`);
  startWhatsApp().catch((e) => console.error("[bridge] Erro ao iniciar Baileys:", e));
});
