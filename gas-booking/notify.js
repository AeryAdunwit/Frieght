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
    sendEmailNotification(data);
    sendLineNotification(buildLineMessage(data));
  } catch (err) {
    Logger.log('sendNotifications error: ' + err.message);
  }
}

function getTodaySummary() {
  const sheet = ss.getSheetByName('บันทึกข้อมูล');
  if (!sheet || sheet.getLastRow() < 2) return { count: 0, items: [] };

  const todayStr = Utilities.formatDate(new Date(), 'GMT+7', 'dd/MM/yyyy');
  const rows = sheet.getRange(2, 1, sheet.getLastRow() - 1, sheet.getLastColumn()).getValues();

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

function buildLineMessage(data) {
  let msg = '🚚 การจองใหม่!\n';
  msg += '─────────────────\n';
  msg += '📅 วันที่จอง: ' + data.date + '\n';
  msg += '👤 ผู้จอง: ' + data.name + '\n';
  msg += '🚛 ประเภทรถ: ' + data.cartype + '\n';
  msg += '📋 สินค้า: ' + (data.product || '-') + '\n';
  msg += '📦 จำนวน: ' + data.amount + '\n';
  msg += '⏰ ช่วงเวลา: ' + (data.timeSlot || '-') + '\n';
  msg += '📍 สถานที่: ' + data.location;
  return msg;
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

function sendEmailNotification(data) {
  const subject = '[SiS Freight] จองใหม่: ' + data.name + ' — ' + data.date;

  let html = '<div style="font-family:sans-serif;max-width:560px;color:#333;">';
  html += '<div style="background:#1e1b4b;padding:16px 20px;border-radius:8px 8px 0 0;">'
        + '<h2 style="margin:0;color:#fff;font-size:16px;">🚚 การจองใหม่ — SiS Freight</h2>'
        + '</div>';
  html += '<div style="border:1px solid #e0e0f0;border-top:none;padding:20px;border-radius:0 0 8px 8px;">';
  html += '<table style="border-collapse:collapse;width:100%;">';
  html += _row('📅 วันที่จอง', data.date);
  html += _row('👤 ชื่อผู้จอง', data.name);
  html += _row('🚛 ประเภทรถ', data.cartype);
  html += _row('📋 สินค้า', data.product || '-');
  html += _row('📦 จำนวน', data.amount);
  html += _row('⏰ ช่วงเวลา', data.timeSlot || '-');
  html += _row('📍 สถานที่', data.location);
  html += '</table>';
  html += '<p style="color:#bbb;font-size:11px;margin-top:16px;border-top:1px solid #eee;padding-top:10px;">'
        + 'SiS Freight — Booking System | ส่งโดยอัตโนมัติ</p>';
  html += '</div></div>';

  MailApp.sendEmail({ to: NOTIFY_EMAIL, subject: subject, htmlBody: html });
}

// ─── Upcoming bookings (tomorrow → tomorrow+3) ───────────────────────────────
function getUpcomingBookings() {
  const sheet = ss.getSheetByName('บันทึกข้อมูล');
  if (!sheet || sheet.getLastRow() < 2) return [];

  const now = new Date();
  const tomorrow = new Date(now);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const endDay = new Date(tomorrow);
  endDay.setDate(endDay.getDate() + 3);

  const tFmt = Utilities.formatDate(tomorrow, 'GMT+7', 'yyyyMMdd');
  const eFmt = Utilities.formatDate(endDay,   'GMT+7', 'yyyyMMdd');

  const rows = sheet.getRange(2, 1, sheet.getLastRow() - 1, sheet.getLastColumn()).getValues();

  return rows
    .filter(function(row) {
      if (!row[0]) return false;
      const d = row[0] instanceof Date ? row[0] : new Date(row[0]);
      if (Number.isNaN(d.getTime())) return false;
      const dFmt = Utilities.formatDate(d, 'GMT+7', 'yyyyMMdd');
      return dFmt >= tFmt && dFmt <= eFmt;
    })
    .map(function(row) { return _bookingFromRow(row); })
    .sort(function(a, b) {
      const da = a.date instanceof Date ? a.date : new Date(a.date);
      const db = b.date instanceof Date ? b.date : new Date(b.date);
      return da - db;
    });
}

// ─── Daily summary email — triggered at 17:00 every day ──────────────────────
function sendDailySummaryEmail() {
  const items = getUpcomingBookings();
  const now = new Date();
  const todayStr = Utilities.formatDate(now, 'GMT+7', 'dd/MM/yyyy');

  const tomorrow = new Date(now);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const endDay = new Date(tomorrow);
  endDay.setDate(endDay.getDate() + 3);
  const rangeStr = Utilities.formatDate(tomorrow, 'GMT+7', 'dd/MM/yyyy')
                 + ' – ' + Utilities.formatDate(endDay, 'GMT+7', 'dd/MM/yyyy');

  const subject = '[SiS Freight] สรุปการจอง ' + rangeStr + ' (' + items.length + ' รายการ)';

  // Group by date string
  const groups = {};
  const order = [];
  items.forEach(function(item) {
    const d = item.date instanceof Date
      ? Utilities.formatDate(item.date, 'GMT+7', 'dd/MM/yyyy')
      : String(item.date);
    if (!groups[d]) { groups[d] = []; order.push(d); }
    groups[d].push(item);
  });

  let html = '<div style="font-family:sans-serif;max-width:700px;color:#333;">';
  html += '<div style="background:#1e1b4b;padding:16px 20px;border-radius:8px 8px 0 0;display:flex;justify-content:space-between;align-items:center;">'
        + '<h2 style="margin:0;color:#fff;font-size:16px;">📊 สรุปการจอง — 4 วันข้างหน้า</h2>'
        + '<span style="color:rgba(255,255,255,.6);font-size:12px;">' + rangeStr + '</span>'
        + '</div>';
  html += '<div style="border:1px solid #e0e0f0;border-top:none;padding:20px;border-radius:0 0 8px 8px;">';

  if (items.length === 0) {
    html += '<p style="color:#999;text-align:center;padding:20px 0;">ไม่มีรายการจองในช่วงนี้</p>';
  } else {
    order.forEach(function(dateStr) {
      const dayItems = groups[dateStr];
      const isSpecialDay = dayItems.some(function(it) {
        return ['กรุงเทพมหานคร','นนทบุรี','สมุทรปราการ','ปทุมธานี'].indexOf(it.location) !== -1;
      });

      html += '<h3 style="margin:16px 0 8px;color:#1e1b4b;font-size:14px;border-bottom:2px solid #e0e0f0;padding-bottom:6px;">'
            + '📅 ' + dateStr + ' <span style="font-weight:400;color:#94a3b8;font-size:12px;">(' + dayItems.length + ' รายการ)</span>'
            + '</h3>';
      html += '<table style="border-collapse:collapse;width:100%;font-size:13px;margin-bottom:8px;">';
      html += '<thead><tr style="background:#f1f5f9;color:#475569;">'
            + '<th style="padding:6px 10px;border:1px solid #e2e8f0;text-align:left;">#</th>'
            + '<th style="padding:6px 10px;border:1px solid #e2e8f0;text-align:left;">ชื่อผู้จอง</th>'
            + '<th style="padding:6px 10px;border:1px solid #e2e8f0;text-align:left;">ประเภทรถ</th>'
            + '<th style="padding:6px 10px;border:1px solid #e2e8f0;text-align:left;">สินค้า</th>'
            + '<th style="padding:6px 10px;border:1px solid #e2e8f0;text-align:center;">จำนวน</th>'
            + '<th style="padding:6px 10px;border:1px solid #e2e8f0;text-align:left;">ช่วงเวลา</th>'
            + '<th style="padding:6px 10px;border:1px solid #e2e8f0;text-align:left;">สถานที่</th>'
            + '</tr></thead><tbody>';

      dayItems.forEach(function(item, i) {
        const isSpec = ['กรุงเทพมหานคร','นนทบุรี','สมุทรปราการ','ปทุมธานี'].indexOf(item.location) !== -1;
        const locBg  = isSpec ? '#fff7ed' : '#eff6ff';
        const locClr = isSpec ? '#c2410c'  : '#1d4ed8';
        const rowBg  = i % 2 === 0 ? '#fff' : '#f8fafc';
        html += '<tr style="background:' + rowBg + ';">'
              + '<td style="padding:6px 10px;border:1px solid #e2e8f0;color:#94a3b8;">' + (i + 1) + '</td>'
              + '<td style="padding:6px 10px;border:1px solid #e2e8f0;font-weight:600;">' + _esc(String(item.name)) + '</td>'
              + '<td style="padding:6px 10px;border:1px solid #e2e8f0;">' + _esc(String(item.cartype)) + '</td>'
              + '<td style="padding:6px 10px;border:1px solid #e2e8f0;">' + _esc(String(item.product || '-')) + '</td>'
              + '<td style="padding:6px 10px;border:1px solid #e2e8f0;text-align:center;">' + _esc(String(item.amount)) + '</td>'
              + '<td style="padding:6px 10px;border:1px solid #e2e8f0;">' + _esc(String(item.timeSlot || '-')) + '</td>'
              + '<td style="padding:6px 10px;border:1px solid #e2e8f0;">'
              + '<span style="background:' + locBg + ';color:' + locClr + ';padding:2px 8px;border-radius:999px;font-size:11px;">'
              + _esc(String(item.location)) + '</span></td>'
              + '</tr>';
      });

      html += '</tbody></table>';
    });

    html += '<div style="margin-top:16px;padding:12px 16px;background:#f1f5f9;border-radius:8px;font-size:13px;color:#475569;">'
          + '📦 รวมทั้งหมด <strong>' + items.length + ' รายการ</strong> ใน 4 วันข้างหน้า'
          + '</div>';
  }

  html += '<p style="color:#bbb;font-size:11px;margin-top:16px;border-top:1px solid #eee;padding-top:10px;">'
        + 'SiS Freight — Daily Summary | ส่งอัตโนมัติทุกวัน 17:00 น.</p>';
  html += '</div></div>';

  MailApp.sendEmail({ to: NOTIFY_EMAIL, subject: subject, htmlBody: html });
  Logger.log('Daily summary sent: ' + items.length + ' items (' + rangeStr + ')');
}

// ─── One-time setup: สร้าง trigger สำหรับ daily summary ─────────────────────
// รันฟังก์ชันนี้ครั้งเดียวใน Apps Script editor เพื่อสร้าง trigger
function createDailySummaryTrigger() {
  // ลบ trigger เก่าของ sendDailySummaryEmail ก่อน (ถ้ามี)
  ScriptApp.getProjectTriggers().forEach(function(t) {
    if (t.getHandlerFunction() === 'sendDailySummaryEmail') {
      ScriptApp.deleteTrigger(t);
    }
  });
  // สร้างใหม่ ทุกวัน 17:00–18:00 (timezone ตาม script settings → ตั้งให้เป็น GMT+7)
  ScriptApp.newTrigger('sendDailySummaryEmail')
    .timeBased()
    .everyDays(1)
    .atHour(17)
    .create();
  Logger.log('Daily summary trigger created: every day at 17:00');
}

function _row(label, value) {
  return '<tr>'
    + '<td style="padding:8px 12px;border:1px solid #f0e6e5;background:#faf6f5;font-weight:600;width:150px;color:#8c3b38;">' + label + '</td>'
    + '<td style="padding:8px 12px;border:1px solid #f0e6e5;">' + _esc(String(value || '')) + '</td>'
    + '</tr>';
}

function _bookingFromRow(row) {
  const isExpanded = row.length >= 7;
  return {
    date: row[0],
    name: row[1],
    cartype: row[2],
    product: isExpanded ? row[3] : '',
    amount: isExpanded ? row[4] : row[3],
    timeSlot: isExpanded ? row[5] : '',
    location: isExpanded ? row[6] : row[4],
    adminName: row.length >= 9 ? row[8] || '' : ''
  };
}

function _esc(s) {
  return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
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

  Logger.log('Sending test new-booking email to ' + NOTIFY_EMAIL + '...');
  try {
    sendEmailNotification(testData);
    Logger.log('Email (new booking): OK ✅');
  } catch (e) {
    Logger.log('Email ERROR ❌: ' + e.message);
  }

  Logger.log('Sending test daily summary email...');
  try {
    sendDailySummaryEmail();
    Logger.log('Email (daily summary): OK ✅');
  } catch (e) {
    Logger.log('Daily summary ERROR ❌: ' + e.message);
  }

  Logger.log('Sending test LINE message...');
  try {
    sendLineNotification(buildLineMessage(testData));
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
    const item = _bookingFromRow(row);
    const d = item.date instanceof Date
      ? Utilities.formatDate(item.date, 'GMT+7', 'dd/MM/yyyy')
      : String(item.date);
    msg += (i + 1) + '. ' + item.name + ' | ' + d + '\n';
    msg += '   🚛 ' + item.cartype + ' | 📋 ' + (item.product || '-') + ' | 📦 ' + item.amount + '\n';
    msg += '   ⏰ ' + (item.timeSlot || '-') + ' | 📍 ' + item.location + '\n';
  });

  return msg.trim();
}
