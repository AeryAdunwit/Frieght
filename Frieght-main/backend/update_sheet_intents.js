const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const SHEET_ID = process.argv[2] || "1-dGeRU60BzTBRxDVWB1DmGLZfPXEcPSHNjUsKqD-sUQ";
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

async function getAccessToken(creds) {
  const now = Math.floor(Date.now() / 1000);
  const header = { alg: "RS256", typ: "JWT" };
  const claim = {
    iss: creds.client_email,
    scope: "https://www.googleapis.com/auth/spreadsheets",
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

function normalizeText(value) {
  return (value || "").trim().replace(/\s+/g, " ");
}

const INTENT_MAP = {
  solar: {
    "บริการส่ง Solar ผ่าน Hub คืออะไร": "definition",
    "งานแบบไหนเหมาะกับ Solar ผ่าน Hub": "fit_use_case",
    "งานแบบไหนเหมาะกับบริการ Solar Hub": "fit_use_case",
    "ถ้าจะใช้บริการ Solar ผ่าน Hub ต้องเตรียมข้อมูลอะไรบ้าง": "required_info",
    "ถ้าต้องการใช้บริการ Solar Hub ต้องเตรียมข้อมูลอะไรบ้าง": "required_info",
    "Solar ผ่าน Hub คิดราคายังไง": "pricing",
    "Solar Hub มีข้อจำกัดอะไรบ้าง": "limitations",
    "Solar Hub มีข้อจำกัดอะไรที่ควรรู้": "limitations",
  },
  pricing: {
    "คิดราคาค่าส่งจากอะไรบ้าง": "pricing_factor",
    "ราคาค่าขนส่งคิดจากอะไร": "pricing_factor",
    "ถ้าจะขอประเมินราคา ต้องส่งข้อมูลอะไรบ้าง": "quote_input",
    "ถ้าต้องการใบเสนอราคา ต้องแจ้งอะไรบ้าง": "quote_input",
    "มีราคากลางไหม": "pricing_policy",
    "มีขั้นต่ำหรือไม่": "pricing_policy",
    "งานแบบไหนต้องประเมินหน้างานก่อน": "site_check",
  },
  booking: {
    "ถ้าจะจองงานต้องทำอย่างไร": "booking_step",
    "ขั้นตอนการจองขนส่งมีอะไรบ้าง": "booking_step",
    "ต้องใช้ข้อมูลอะไรในการจอง": "booking_input",
    "ถ้าจะจองรถเหมาคัน ต้องเตรียมข้อมูลอะไร": "booking_input",
    "ควรจองล่วงหน้าไหม": "booking_timing",
    "จองล่วงหน้าได้ไหม": "booking_timing",
    "งานเหมาคันหรือรถใหญ่ต้องแจ้งอะไรเพิ่ม": "special_case",
  },
  claim: {
    "สินค้าชำรุดต้องทำอย่างไร": "claim_step",
    "ถ้าสินค้าเสียหายต้องทำอย่างไร": "claim_step",
    "ถ้าของหายหรือส่งผิดต้องแจ้งอะไรบ้าง": "claim_input",
    "ถ้าของหายต้องแจ้งข้อมูลอะไร": "claim_input",
    "เคลมต้องใช้หลักฐานอะไร": "claim_evidence",
    "ใช้เวลาตรวจสอบประมาณกี่วัน": "claim_timeline",
    "ใช้เวลาตรวจสอบเคลมนานไหม": "claim_timeline",
  },
  coverage: {
    "ส่งได้ทั่วประเทศไหม": "nationwide",
    "มีส่งต่างจังหวัดไหม": "upcountry",
    "ต่างจังหวัดรับงานไหม": "upcountry",
    "พื้นที่ไหนต้องเช็กก่อน": "restricted_area",
    "ถ้าปลายทางยังไม่แน่ใจต้องทำอย่างไร": "check_area",
  },
  documents: {
    "ต้องใช้เอกสารอะไรบ้าง": "document_list",
    "เอกสารไหนจำเป็น": "required_document",
    "ต้องใช้ POD หรือไม่": "pod",
    "ถ้าเอกสารไม่ครบต้องทำอย่างไร": "missing_document",
  },
  timeline: {
    "ปกติใช้เวลากี่วัน": "transit_time",
    "มีรอบเข้ารับสินค้าไหม": "pickup_window",
    "มีรอบเข้ารับกี่โมง": "pickup_window",
    "ตัดรอบกี่โมง": "cutoff",
    "อะไรทำให้ส่งช้ากว่าปกติ": "delay_factor",
  },
  general: {
    "SiS Freight มีบริการอะไรบ้าง": "service_overview",
    "ถ้าต้องการเจ้าหน้าที่ต้องทำอย่างไร": "handoff",
    "งานแบบไหนควรทักมาสอบถามก่อน": "consult_case",
  },
};

async function main() {
  const env = loadEnvFile(ENV_PATH);
  const credsRaw = env.GOOGLE_CREDENTIALS;
  if (!credsRaw) throw new Error("Missing GOOGLE_CREDENTIALS in .env");
  const creds = JSON.parse(credsRaw);
  const token = await getAccessToken(creds);
  const headers = {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };

  const spreadsheet = await fetchJson(`https://sheets.googleapis.com/v4/spreadsheets/${SHEET_ID}`, {
    headers,
  });

  const updates = [];

  for (const sheet of spreadsheet.sheets || []) {
    const title = sheet.properties.title;
    const intentMap = INTENT_MAP[title];
    if (!intentMap) continue;

    const encodedRange = encodeURIComponent(`'${title}'!A:E`);
    const valuesResp = await fetchJson(
      `https://sheets.googleapis.com/v4/spreadsheets/${SHEET_ID}/values/${encodedRange}`,
      { headers },
    );
    const values = valuesResp.values || [];
    if (!values.length) continue;

    const output = [["intent"]];
    for (let i = 1; i < values.length; i += 1) {
      const question = normalizeText(values[i][0]);
      const intent = intentMap[question] || "";
      output.push([intent]);
    }

    updates.push({
      range: `'${title}'!D1:D${output.length}`,
      values: output,
    });
  }

  if (!updates.length) {
    console.log("No matching tabs found to update.");
    return;
  }

  const result = await fetchJson(
    `https://sheets.googleapis.com/v4/spreadsheets/${SHEET_ID}/values:batchUpdate`,
    {
      method: "POST",
      headers,
      body: JSON.stringify({
        valueInputOption: "RAW",
        data: updates,
      }),
    },
  );

  console.log(`Updated ${result.totalUpdatedCells} cells across ${updates.length} tabs.`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
