// ─────────────────────────────────────────────────────────────────────────────
// notify.js — Email + LINE Messaging API notifications
//
// ⚠️  LINE Notify ปิดบริการถาวรแล้ว (มีนาคม 2025) — ต้องใช้ LINE Messaging API แทน
//
// Setup (ทำครั้งเดียวใน Apps Script editor):
//   Extensions → Apps Script → ⚙ Project Settings → Script Properties → Add:
//
//   LINE_CHANNEL_ACCESS_TOKEN  →  Channel Access Token จาก LINE Developers Console
//                                  (developers.line.biz → Messaging API → Channel access token)
//   LINE_TARGET_ID             →  Group ID ของ LINE group ที่ต้องการส่ง (ขึ้นต้นด้วย C...)
//
// วิธีหา LINE_TARGET_ID (Group ID):
//   1. สร้าง LINE Official Account ที่ developers.line.biz → เปิด Messaging API
//   2. ตั้ง Webhook URL (ใช้ webhook.site ชั่วคราวได้)
//   3. เพิ่ม LINE Bot เข้า group → ส่งข้อความใน group
//   4. Group ID จะอยู่ใน webhook payload: source.groupId (ขึ้นต้นด้วย C)
// ─────────────────────────────────────────────────────────────────────────────

const NOTIFY_EMAIL = 'Sorravit_l@sisthai.com';

function sendNotifications(data) {
  try {
    const summary = getTodaySummary();
    sendEmailNotification(data, summary);
    sendLineNotification(buildLineMessage(data, summary));
  } catch (err) {
    Logger.log('sendNotifications error: ' + err.message);
  }
}

function getTodaySummary() {
  const sheet = ss.getSheetByName('บันทึกข้อมูล');
  if (!sheet || sheet.getLastRow() < 2) return { count: 0, items: [] };

  const todayStr = Utilities.formatDate(new Date(), 'GMT+7', 'dd/MM/yyyy');
  const rows = sheet.getRange(2, 1, sheet.getLastRow() - 1, 5).getValues();

  const items = rows.filter(function (row) {
    if (!row[0]) return false;
    try {
      const d = row[0] instanceof Date ? row[0] : new Date(row[0]);
      return Utilities.formatDate(d, 'GMT+7', 'dd/MM/yyyy') === todayStr;
    } catch (e) {
      return false;
    }
  });

  return { count: items.length, items: items };
}

function buildLineMessage(data, summary) {
  const todayStr = Utilities.formatDate(new Date(), 'GMT+7', 'dd/MM/yyyy');

  let msg = '🚚 การจองใหม่!\n';
  msg += '─────────────────\n';
  msg += '📅 วันที่จอง: ' + data.date + '\n';
  msg += '👤 ผู้จอง: ' + data.name + '\n';
  msg += '🚛 ประเภทรถ: ' + data.cartype + '\n';
  msg += '📦 จำนวน: ' + data.amount + '\n';
  msg += '📍 สถานที่: ' + data.location + '\n';
  msg += '─────────────────\n';
  msg += '📊 สรุปวันนี้ (' + todayStr + '): ' + summary.count + ' รายการ\n';

  summary.items.forEach(function (row, i) {
    const d = row[0] instanceof Date
      ? Utilities.formatDate(row[0], 'GMT+7', 'dd/MM/yyyy')
      : String(row[0]);
    msg += (i + 1) + '. ' + row[1] + ' | ' + row[2] + ' | ' + row[4] + '\n';
  });

  return msg.trim();
}

function sendLineNotification(text) {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty('LINE_CHANNEL_ACCESS_TOKEN');
  const targetId = props.getProperty('LINE_TARGET_ID');

  if (!token || !targetId) {
    Logger.log('LINE ยังไม่ได้ตั้งค่า: กรุณาเพิ่ม LINE_CHANNEL_ACCESS_TOKEN และ LINE_TARGET_ID ใน Script Properties');
    return;
  }

  const res = UrlFetchApp.fetch('https://api.line.me/v2/bot/message/push', {
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + token
    },
    payload: JSON.stringify({
      to: targetId,
      messages: [{ type: 'text', text: text }]
    }),
    muteHttpExceptions: true
  });

  if (res.getResponseCode() !== 200) {
    Logger.log('LINE API error ' + res.getResponseCode() + ': ' + res.getContentText());
  }
}

function sendEmailNotification(data, summary) {
  const todayStr = Utilities.formatDate(new Date(), 'GMT+7', 'dd/MM/yyyy');
  const subject = '[SiS Freight] จองใหม่: ' + data.name + ' — ' + data.date;

  let html = '<div style="font-family:sans-serif;max-width:620px;color:#333;">';

  html += '<div style="background:#8c3b38;padding:16px 20px;border-radius:8px 8px 0 0;">'
        + '<h2 style="margin:0;color:#fff;font-size:18px;">🚚 การจองใหม่ — SiS Freight</h2>'
        + '</div>';

  html += '<div style="border:1px solid #f0e6e5;border-top:none;padding:20px;border-radius:0 0 8px 8px;">';

  html += '<table style="border-collapse:collapse;width:100%;margin-bottom:24px;">';
  html += _row('📅 วันที่จอง', data.date);
  html += _row('👤 ชื่อผู้จอง', data.name);
  html += _row('🚛 ประเภทรถ', data.cartype);
  html += _row('📦 จำนวน', data.amount);
  html += _row('📍 สถานที่', data.location);
  html += '</table>';

  html += '<h3 style="color:#8c3b38;margin:0 0 10px;">📊 สรุปรายการวันนี้ (' + todayStr + ') — ' + summary.count + ' รายการ</h3>';

  if (summary.items.length > 0) {
    html += '<table style="border-collapse:collapse;width:100%;font-size:13px;">'
          + '<thead><tr style="background:#f5e0df;color:#8c3b38;">'
          + '<th style="padding:7px 10px;border:1px solid #e8d5d4;text-align:left;">#</th>'
          + '<th style="padding:7px 10px;border:1px solid #e8d5d4;text-align:left;">วันที่</th>'
          + '<th style="padding:7px 10px;border:1px solid #e8d5d4;text-align:left;">ชื่อ</th>'
          + '<th style="padding:7px 10px;border:1px solid #e8d5d4;text-align:left;">ประเภทรถ</th>'
          + '<th style="padding:7px 10px;border:1px solid #e8d5d4;text-align:left;">จำนวน</th>'
          + '<th style="padding:7px 10px;border:1px solid #e8d5d4;text-align:left;">สถานที่</th>'
          + '</tr></thead><tbody>';

    summary.items.forEach(function (row, i) {
      const d = row[0] instanceof Date
        ? Utilities.formatDate(row[0], 'GMT+7', 'dd/MM/yyyy')
        : String(row[0]);
      const bg = i % 2 === 0 ? '#fff' : '#faf6f5';
      html += '<tr style="background:' + bg + ';">'
            + '<td style="padding:6px 10px;border:1px solid #e8d5d4;">' + (i + 1) + '</td>'
            + '<td style="padding:6px 10px;border:1px solid #e8d5d4;">' + _esc(d) + '</td>'
            + '<td style="padding:6px 10px;border:1px solid #e8d5d4;">' + _esc(String(row[1])) + '</td>'
            + '<td style="padding:6px 10px;border:1px solid #e8d5d4;">' + _esc(String(row[2])) + '</td>'
            + '<td style="padding:6px 10px;border:1px solid #e8d5d4;">' + _esc(String(row[3])) + '</td>'
            + '<td style="padding:6px 10px;border:1px solid #e8d5d4;">' + _esc(String(row[4])) + '</td>'
            + '</tr>';
    });

    html += '</tbody></table>';
  } else {
    html += '<p style="color:#999;">ไม่พบรายการอื่นในวันนี้</p>';
  }

  html += '<p style="color:#bbb;font-size:11px;margin-top:20px;border-top:1px solid #f0e6e5;padding-top:10px;">'
        + 'SiS Freight — Booking System | ส่งโดยอัตโนมัติ</p>';
  html += '</div></div>';

  MailApp.sendEmail({ to: NOTIFY_EMAIL, subject: subject, htmlBody: html });
}

function _row(label, value) {
  return '<tr>'
    + '<td style="padding:8px 12px;border:1px solid #f0e6e5;background:#faf6f5;font-weight:600;width:150px;color:#8c3b38;">' + label + '</td>'
    + '<td style="padding:8px 12px;border:1px solid #f0e6e5;">' + _esc(String(value || '')) + '</td>'
    + '</tr>';
}

function _esc(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ─────────────────────────────────────────────────────────────────────────────
// LINE Webhook — รับข้อความจาก group แล้ว reply summary
//
// Setup เพิ่มเติม:
//   LINE Developers Console → Messaging API → Webhook settings
//   → Webhook URL: URL ของ GAS web app นี้ (จาก Extensions → Deploy → Manage deployments)
//   → เปิด "Use webhook"
// ─────────────────────────────────────────────────────────────────────────────

function handleLineWebhook(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    const events = body.events || [];

    events.forEach(function (event) {
      if (event.type !== 'message' || event.message.type !== 'text') return;
      const text = event.message.text.trim().toLowerCase();
      if (text !== 'work') return;

      const summary = getTodaySummary();
      replyLineMessage(event.replyToken, buildSummaryMessage(summary));
    });
  } catch (err) {
    Logger.log('handleLineWebhook error: ' + err.message);
  }

  return ContentService.createTextOutput(JSON.stringify({ status: 'ok' }))
    .setMimeType(ContentService.MimeType.JSON);
}

function replyLineMessage(replyToken, text) {
  const token = PropertiesService.getScriptProperties().getProperty('LINE_CHANNEL_ACCESS_TOKEN');
  if (!token) {
    Logger.log('LINE_CHANNEL_ACCESS_TOKEN ไม่ได้ตั้งค่า');
    return;
  }

  const res = UrlFetchApp.fetch('https://api.line.me/v2/bot/message/reply', {
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + token
    },
    payload: JSON.stringify({
      replyToken: replyToken,
      messages: [{ type: 'text', text: text }]
    }),
    muteHttpExceptions: true
  });

  if (res.getResponseCode() !== 200) {
    Logger.log('LINE reply error ' + res.getResponseCode() + ': ' + res.getContentText());
  }
}

function keepWarm() {
  Logger.log('keepWarm ping ' + new Date().toISOString());
}

function testNotify() {
  const props = PropertiesService.getScriptProperties().getProperties();
  Logger.log('Script Properties: ' + JSON.stringify(Object.keys(props)));

  const token = PropertiesService.getScriptProperties().getProperty('LINE_CHANNEL_ACCESS_TOKEN');
  Logger.log('LINE token set: ' + (token ? 'YES (' + token.substring(0, 10) + '...)' : 'NO ❌'));

  const testData = {
    date: Utilities.formatDate(new Date(), 'GMT+7', 'dd/MM/yyyy'),
    name: 'ทดสอบระบบ',
    cartype: 'รถ 6 ล้อ',
    amount: '1',
    location: 'กรุงเทพมหานคร'
  };

  Logger.log('Sending test email to ' + NOTIFY_EMAIL + '...');
  try {
    const summary = getTodaySummary();
    sendEmailNotification(testData, summary);
    Logger.log('Email: OK ✅');
  } catch (e) {
    Logger.log('Email ERROR ❌: ' + e.message);
  }

  Logger.log('Sending test LINE message...');
  try {
    sendLineNotification(buildLineMessage(testData, { count: 1, items: [] }));
    Logger.log('LINE: OK ✅ (ดู error log ถ้าไม่ได้รับ)');
  } catch (e) {
    Logger.log('LINE ERROR ❌: ' + e.message);
  }
}

function buildSummaryMessage(summary) {
  const todayStr = Utilities.formatDate(new Date(), 'GMT+7', 'dd/MM/yyyy');
  let msg = '📊 สรุปการจองวันนี้\n';
  msg += '(' + todayStr + ')\n';
  msg += '─────────────────\n';
  msg += 'รวมทั้งหมด: ' + summary.count + ' รายการ\n';

  if (summary.count === 0) {
    msg += '\nยังไม่มีการจองในวันนี้ครับ';
    return msg;
  }

  msg += '─────────────────\n';
  summary.items.forEach(function (row, i) {
    const d = row[0] instanceof Date
      ? Utilities.formatDate(row[0], 'GMT+7', 'dd/MM/yyyy')
      : String(row[0]);
    msg += (i + 1) + '. ' + row[1] + ' | ' + d + '\n';
    msg += '   🚛 ' + row[2] + ' | 📦 ' + row[3] + ' แผ่น | 📍 ' + row[4] + '\n';
  });

  return msg.trim();
}
