const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const ENV_PATH = path.resolve(__dirname, "..", ".env");

function loadEnvFile(filePath) {
  const raw = fs.readFileSync(filePath, "utf8");
  const env = {};
  for (const line of raw.split(/\r?\n/)) {
    if (!line || line.trim().startsWith("#")) continue;
    const idx = line.indexOf("=");
    if (idx === -1) continue;
    const key = line.slice(0, idx).trim();
    let value = line.slice(idx + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    } else {
      value = value.replace(/^['"]/, "").replace(/['"]$/, "");
    }
    env[key] = value;
  }
  return env;
}

function base64url(input) {
  return Buffer.from(input).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

async function fetchJson(url, options = {}) {
  const res = await fetch(url, options);
  const text = await res.text();
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

async function getSheetsAccessToken(creds) {
  const now = Math.floor(Date.now() / 1000);
  const header = { alg: "RS256", typ: "JWT" };
  const claim = {
    iss: creds.client_email,
    scope: "https://www.googleapis.com/auth/spreadsheets.readonly",
    aud: "https://oauth2.googleapis.com/token",
    exp: now + 3600,
    iat: now,
  };

  const unsigned = `${base64url(JSON.stringify(header))}.${base64url(JSON.stringify(claim))}`;
  const signer = crypto.createSign("RSA-SHA256");
  signer.update(unsigned);
  signer.end();
  const signature = signer.sign(creds.private_key);
  const jwt = `${unsigned}.${base64url(signature)}`;

  const body = new URLSearchParams({
    grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
    assertion: jwt,
  });

  const tokenResp = await fetchJson("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });

  return tokenResp.access_token;
}

async function loadKnowledgeRows(sheetId, creds) {
  const token = await getSheetsAccessToken(creds);
  const headers = { Authorization: `Bearer ${token}` };
  const spreadsheet = await fetchJson(`https://sheets.googleapis.com/v4/spreadsheets/${sheetId}`, { headers });

  const rows = [];
  for (const sheet of spreadsheet.sheets || []) {
    const topic = sheet.properties.title;
    const range = encodeURIComponent(`'${topic}'!A:Z`);
    const valuesResp = await fetchJson(
      `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}/values/${range}`,
      { headers },
    );
    const values = valuesResp.values || [];
    if (values.length < 2) continue;

    const headersRow = values[0].map((v) => String(v || "").trim().toLowerCase());
    if (!headersRow.includes("question") || !headersRow.includes("answer")) continue;

    for (let i = 1; i < values.length; i += 1) {
      const entry = {
        topic,
        row_index: i,
        question: "",
        answer: "",
        keywords: "",
        intent: "",
        active: "",
      };
      headersRow.forEach((header, idx) => {
        entry[header] = idx < values[i].length ? String(values[i][idx] || "").trim() : "";
      });
      if (entry.active.toLowerCase() === "no") continue;
      if (entry.question && entry.answer) rows.push(entry);
    }
  }

  return rows;
}

async function embedText(apiKey, model, text) {
  const result = await fetchJson(
    `https://generativelanguage.googleapis.com/v1beta/${model}:embedContent?key=${apiKey}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model,
        content: { parts: [{ text }] },
        outputDimensionality: 768,
      }),
    },
  );
  return result.embedding.values;
}

async function upsertKnowledgeRow(env, payload) {
  const url = `${env.SUPABASE_URL}/rest/v1/knowledge_base`;
  await fetchJson(url, {
    method: "POST",
    headers: {
      apikey: env.SUPABASE_SERVICE_KEY,
      Authorization: `Bearer ${env.SUPABASE_SERVICE_KEY}`,
      "Content-Type": "application/json",
      Prefer: "resolution=merge-duplicates,return=minimal",
    },
    body: JSON.stringify(payload),
  });
}

async function main() {
  const env = loadEnvFile(ENV_PATH);
  const required = ["SHEET_ID", "GOOGLE_CREDENTIALS", "GEMINI_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_KEY"];
  for (const key of required) {
    if (!env[key]) throw new Error(`Missing ${key} in .env`);
  }

  const creds = JSON.parse(env.GOOGLE_CREDENTIALS);
  const model = env.EMBEDDING_MODEL || "models/gemini-embedding-001";
  const rows = await loadKnowledgeRows(env.SHEET_ID, creds);
  console.log(`Syncing ${rows.length} rows...`);

  let synced = 0;
  for (const row of rows) {
    const contentParts = [`Q: ${row.question}`, `A: ${row.answer}`];
    if (row.intent) contentParts.push(`Intent: ${row.intent}`);
    if (row.keywords) contentParts.push(`Keywords: ${row.keywords}`);
    const content = contentParts.join("\n");
    const embedding = await embedText(env.GEMINI_API_KEY, model, content);
    const payload = {
      id: `${row.topic}_${row.row_index}`,
      topic: row.topic,
      question: row.question,
      answer: row.answer,
      intent: row.intent || "",
      content,
      embedding,
    };
    await upsertKnowledgeRow(env, payload);
    synced += 1;
  }

  console.log(`Done. ${synced} rows synced to Supabase.`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
