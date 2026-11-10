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
const fs = require("fs");
const path = require("path");
const pino = require("pino");
const QRCode = require("qrcode");
const qrcodeTerminal = require("qrcode-terminal");
const {
  default: makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
  extractMessageContent,
  normalizeMessageContent,
  jidNormalizedUser,
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
const LID_MAP_FILE = path.join(AUTH_DIR, "lid_map.json");
const PROCESSED_IDS_FILE = path.join(AUTH_DIR, "processed_ids.json");

const app = express();
app.use(express.json({ limit: "2mb" }));

let sock = null;
let connectionStatus = "initializing";
let qrDataUrl = null;
let connectedPhone = null;
let connectedLid = null;

// Guarda IDs e assinaturas curtas enviados via API (/send/text) antes mesmo de sendMessage resolver
const sentByApiIds = new Set();
const recentApiSignatures = new Map(); // sig -> expiresAtMs
const lidToPhoneMap = new Map(); // normalizedLid (e.g. 1667...@lid) -> phone digits (5519...)
const phoneToLidMap = new Map(); // phone digits -> normalizedLid
const processedMsgIds = new Set(); // evita replay de mensagens antigas após reconexão (code=408)

function loadProcessedIds() {
  try {
    if (!fs.existsSync(PROCESSED_IDS_FILE)) return;
    const raw = JSON.parse(fs.readFileSync(PROCESSED_IDS_FILE, "utf8"));
    if (Array.isArray(raw)) {
      for (const id of raw.slice(-800)) {
        if (id) processedMsgIds.add(String(id));
      }
    }
  } catch (_) {}
}

function recordProcessedId(msgId) {
  if (!msgId) return;
  processedMsgIds.add(msgId);
  while (processedMsgIds.size > 1000) {
    const first = processedMsgIds.values().next().value;
    processedMsgIds.delete(first);
  }
  try {
    fs.mkdirSync(AUTH_DIR, { recursive: true });
    fs.writeFileSync(PROCESSED_IDS_FILE, JSON.stringify(Array.from(processedMsgIds).slice(-800)), "utf8");
  } catch (_) {}
}

loadProcessedIds();

function digitsOnly(val) {
  return String(val || "")
    .split("@")[0]
    .split(":")[0]
    .replace(/\D/g, "");
}

function normalizeLidJid(val) {
  const d = digitsOnly(val);
  return d ? `${d}@lid` : "";
}

function loadLidMappings() {
  try {
    if (!fs.existsSync(LID_MAP_FILE)) return;
    const raw = JSON.parse(fs.readFileSync(LID_MAP_FILE, "utf8"));
    if (raw && typeof raw === "object") {
      for (const [lid, phone] of Object.entries(raw)) {
        const normLid = normalizeLidJid(lid);
        const normPhone = digitsOnly(phone);
        if (normLid && normPhone) {
          lidToPhoneMap.set(normLid, normPhone);
          phoneToLidMap.set(normPhone, normLid);
        }
      }
    }
  } catch (_) {}
}

function saveLidMappings() {
  try {
    fs.mkdirSync(AUTH_DIR, { recursive: true });
    const obj = {};
    for (const [lid, phone] of lidToPhoneMap.entries()) {
      obj[lid] = phone;
    }
    fs.writeFileSync(LID_MAP_FILE, JSON.stringify(obj, null, 2), "utf8");
  } catch (_) {}
}

function recordLidMapping(lidVal, phoneVal) {
  if (!lidVal || !phoneVal) return false;
  if (!String(lidVal).includes("@lid")) return false;
  const normLid = normalizeLidJid(lidVal);
  const phoneDigits = digitsOnly(phoneVal);
  if (!normLid || !phoneDigits || phoneDigits.length < 10) return false;
  const prev = lidToPhoneMap.get(normLid);
  lidToPhoneMap.set(normLid, phoneDigits);
  phoneToLidMap.set(phoneDigits, normLid);
  if (prev !== phoneDigits) {
    saveLidMappings();
    console.log(`[bridge] Mapeado LID ${normLid} <-> Telefone ${phoneDigits}`);
  }
  return true;
}

loadLidMappings();

function pruneRecentApiSignatures() {
  const now = Date.now();
  for (const [k, exp] of recentApiSignatures.entries()) {
    if (exp <= now) recentApiSignatures.delete(k);
  }
}

function markRecentApiSend(phoneDigits, text) {
  pruneRecentApiSignatures();
  const cleanText = String(text || "").trim();
  if (!cleanText) return;
  const ttl = Date.now() + 30000;
  if (phoneDigits) {
    recentApiSignatures.set(`${phoneDigits}::${cleanText}`, ttl);
  }
  recentApiSignatures.set(`*::${cleanText}`, ttl);
}

function matchesRecentApiSend(chatidOrDigits, text) {
  pruneRecentApiSignatures();
  const cleanText = String(text || "").trim();
  if (!cleanText) return false;
  const digits = digitsOnly(chatidOrDigits);
  const now = Date.now();
  if (digits && (recentApiSignatures.get(`${digits}::${cleanText}`) || 0) > now) {
    return true;
  }
  if ((recentApiSignatures.get(`*::${cleanText}`) || 0) > now) {
    return true;
  }
  return false;
}

function extractMessageText(m) {
  if (!m || !m.message) return "";
  let rawMsg = m.message;
  if (rawMsg.deviceSentMessage && rawMsg.deviceSentMessage.message) {
    rawMsg = rawMsg.deviceSentMessage.message;
  }
  const normalized = normalizeMessageContent(rawMsg) || rawMsg;
  const extracted = extractMessageContent(normalized) || normalized;
  if (
    extracted.protocolMessage ||
    extracted.senderKeyDistributionMessage ||
    extracted.reactionMessage
  ) {
    return "";
  }
  return (
    extracted.conversation ||
    extracted.extendedTextMessage?.text ||
    extracted.imageMessage?.caption ||
    extracted.videoMessage?.caption ||
    extracted.documentMessage?.caption ||
    extracted.buttonsResponseMessage?.selectedDisplayText ||
    extracted.listResponseMessage?.title ||
    ""
  ).trim();
}

const messageStore = new Map();

async function getMessage(key) {
  const id = key && key.id;
  if (id && messageStore.has(id)) {
    return messageStore.get(id);
  }
  return undefined;
}

function toWhatsappJid(number) {
  let d = digitsOnly(number);
  if (!d) throw new Error(`Numero invalido: ${number}`);
  // Normalização automática do 9º dígito para celulares do Brasil (DDD 11 a 99)
  if (d.startsWith("55") && d.length === 12) {
    const firstNum = d.substring(4, 5);
    if (["6", "7", "8", "9"].includes(firstNum)) {
      d = d.substring(0, 4) + "9" + d.substring(4);
    }
  } else if (!d.startsWith("55") && d.length === 10) {
    const firstNum = d.substring(2, 3);
    if (["6", "7", "8", "9"].includes(firstNum)) {
      d = "55" + d.substring(0, 2) + "9" + d.substring(2);
    } else {
      d = "55" + d;
    }
  } else if (!d.startsWith("55") && d.length === 11) {
    d = "55" + d;
  }
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
    keepAliveIntervalMs: 20000,
    connectTimeoutMs: 30000,
    retryRequestDelayMs: 500,
    syncFullHistory: false,
    shouldSyncHistoryMessage: () => false,
    shouldIgnoreJid: (jid) =>
      !jid ||
      jid.endsWith("@broadcast") ||
      jid.endsWith("@newsletter") ||
      jid === "status@broadcast",
    getMessage,
  });

  sock.ev.on("creds.update", saveCreds);

  const ingestContacts = (contacts) => {
    for (const c of contacts || []) {
      const id = c && (c.id || c.jid);
      const lid = c && c.lid;
      if (id && lid && String(id).includes("@s.whatsapp.net") && String(lid).includes("@lid")) {
        recordLidMapping(lid, id);
      } else if (id && c && c.phoneNumber && String(id).includes("@lid")) {
        recordLidMapping(id, c.phoneNumber);
      }
    }
  };
  sock.ev.on("contacts.upsert", ingestContacts);
  sock.ev.on("contacts.update", ingestContacts);

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
      connectedLid = sock.user && sock.user.lid ? normalizeLidJid(sock.user.lid) : null;
      if (connectedLid && connectedPhone) {
        recordLidMapping(connectedLid, connectedPhone);
      }
      console.log(`[bridge] WhatsApp conectado com sucesso: ${connectedPhone}${connectedLid ? ` (LID ${connectedLid})` : ""}`);
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
    for (const m of messages || []) {
      const remoteJid = (m.key && m.key.remoteJid) || "";
      if (!remoteJid || remoteJid.endsWith("@g.us") || remoteJid === "status@broadcast") {
        continue;
      }

      const msgId = (m.key && m.key.id) || "";
      if (msgId && m.message) {
        messageStore.set(msgId, m.message);
        if (messageStore.size > 2000) {
          const first = messageStore.keys().next().value;
          messageStore.delete(first);
        }
      }

      if (msgId && processedMsgIds.has(msgId)) {
        continue;
      }

      // Captura mapeamentos LID <-> Telefone presentes nos atributos do envelope Baileys 6.7+
      if (remoteJid.endsWith("@s.whatsapp.net") && m.key && m.key.senderLid) {
        recordLidMapping(m.key.senderLid, remoteJid);
      }

      const fromMe = Boolean(m.key && m.key.fromMe);
      const text = extractMessageText(m);

      // Se não há texto real, descarta imediatamente (ignora syncs internos do Baileys, recibos e pacotes vazios)
      if (!text || text.trim().length === 0) continue;

      const rawTs = m.messageTimestamp;
      const msgTs =
        typeof rawTs === "number"
          ? rawTs
          : rawTs && typeof rawTs.toNumber === "function"
          ? rawTs.toNumber()
          : Number(rawTs || 0);
      const ageSec = msgTs > 0 ? Math.floor(Date.now() / 1000) - msgTs : 0;

      // Resolve chatid telefônico real caso venha como @lid
      let effectiveChatid = remoteJid;
      if (remoteJid.endsWith("@lid")) {
        const normLid = normalizeLidJid(remoteJid);
        const destJid = m.message?.deviceSentMessage?.destinationJid || "";
        const altPhone =
          (m.key && m.key.senderPn) ||
          (m.key && m.key.participantPn) ||
          (m.key && m.key.remoteJidAlt) ||
          (m.key && m.key.participant) ||
          (destJid.endsWith("@s.whatsapp.net") ? destJid : "") ||
          "";
        if (altPhone && altPhone.endsWith("@s.whatsapp.net")) {
          const pDigits = digitsOnly(altPhone);
          effectiveChatid = `${pDigits}@s.whatsapp.net`;
          recordLidMapping(normLid, pDigits);
        } else if (lidToPhoneMap.has(normLid)) {
          effectiveChatid = `${lidToPhoneMap.get(normLid)}@s.whatsapp.net`;
        } else if (lidToPhoneMap.has(remoteJid)) {
          effectiveChatid = `${lidToPhoneMap.get(remoteJid)}@s.whatsapp.net`;
        }
      }

      const wasSentByApi =
        sentByApiIds.has(msgId) ||
        (fromMe && matchesRecentApiSend(effectiveChatid, text));
      if (sentByApiIds.has(msgId)) {
        sentByApiIds.delete(msgId);
      }

      // Bloqueia replay de mensagens antigas / offline após reconexão (ex: code=408)
      if (ageSec > 180) {
        if (msgId) recordProcessedId(msgId);
        console.log(`[bridge] Ignorando replay antigo (${ageSec}s, type=${type}): "${text.substring(0, 40)}"`);
        continue;
      }
      if (fromMe && !wasSentByApi && (type !== "notify" || ageSec > 45)) {
        if (msgId) recordProcessedId(msgId);
        console.log(`[bridge] Ignorando replay fromMe offline/append (type=${type}, age=${ageSec}s): "${text.substring(0, 40)}"`);
        continue;
      }

      if (msgId) {
        recordProcessedId(msgId);
      }

      console.log(
        `[bridge] Mensagem recebida [type=${type}, fromMe=${fromMe}, wasSentByApi=${wasSentByApi}]: ` +
        `remoteJid=${remoteJid} -> effectiveChatid=${effectiveChatid} | texto="${text}"`
      );

      await forwardToFastApi({
        EventType: "messages",
        instanceName: "painel-qr-bridge",
        message: {
          fromMe,
          isGroup: false,
          wasSentByApi,
          type: "text",
          text,
          chatid: effectiveChatid,
          rawRemoteJid: remoteJid,
          senderName: m.pushName || "",
          messageid: msgId,
        },
      });
    }
  });
}

async function resolvePhoneLidBestEffort(jid) {
  try {
    const jidDigits = digitsOnly(jid);
    if (!sock || !jidDigits || phoneToLidMap.has(jidDigits)) return;
    const res = await Promise.race([
      sock.onWhatsApp(jid),
      new Promise((resolve) => setTimeout(() => resolve([]), 1200)),
    ]);
    if (Array.isArray(res)) {
      for (const item of res) {
        if (item && item.lid && item.jid) {
          recordLidMapping(item.lid, item.jid);
        }
      }
    }
  } catch (_) {}
}

app.get("/status", (_req, res) => {
  res.json({
    connected: connectionStatus === "connected",
    status: connectionStatus,
    phone: connectedPhone,
    lid: connectedLid,
    lid_mappings_count: lidToPhoneMap.size,
    qr_data_url: qrDataUrl,
  });
});

app.get("/lids", (_req, res) => {
  const obj = {};
  for (const [k, v] of lidToPhoneMap.entries()) obj[k] = v;
  res.json({ ok: true, count: lidToPhoneMap.size, mappings: obj });
});

app.post("/resolve-lid", async (req, res) => {
  try {
    const { number } = req.body || {};
    if (!number) return res.status(400).json({ error: "number obrigatorio" });
    const jid = toWhatsappJid(number);
    const jidDigits = digitsOnly(jid);
    if (sock && connectionStatus === "connected") {
      await resolvePhoneLidBestEffort(jid);
    }
    return res.json({
      ok: true,
      jid,
      phone: jidDigits,
      lid: phoneToLidMap.get(jidDigits) || null,
    });
  } catch (err) {
    return res.status(400).json({ error: String(err.message || err) });
  }
});

app.post("/send/text", async (req, res) => {
  try {
    if (!sock || connectionStatus !== "connected") {
      return res.status(503).json({ error: "WhatsApp ainda nao conectado via QR Code" });
    }
    const { number, text } = req.body || {};
    const textStr = String(text || "");
    const jid = toWhatsappJid(number);
    const jidDigits = digitsOnly(jid);
    await resolvePhoneLidBestEffort(jid);
    markRecentApiSend(jidDigits, textStr);

    console.log(`[bridge] Enviando mensagem para ${jid} (${jidDigits}): "${textStr.substring(0, 80)}..."`);
    const sent = await sock.sendMessage(jid, { text: textStr });
    const msgId = (sent && sent.key && sent.key.id) || "";
    const sentRemoteJid = (sent && sent.key && sent.key.remoteJid) || "";
    if (sentRemoteJid && sentRemoteJid.endsWith("@lid") && jidDigits) {
      recordLidMapping(sentRemoteJid, jidDigits);
    }
    if (msgId) {
      if (sent && sent.message) {
        messageStore.set(msgId, sent.message);
      } else {
        messageStore.set(msgId, { conversation: textStr });
      }
      if (messageStore.size > 2000) {
        const first = messageStore.keys().next().value;
        messageStore.delete(first);
      }
      sentByApiIds.add(msgId);
      setTimeout(() => sentByApiIds.delete(msgId), 60000);
    }
    return res.json({ ok: true, messageid: msgId, jid });
  } catch (err) {
    console.error("[bridge] Erro ao enviar mensagem:", err);
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
