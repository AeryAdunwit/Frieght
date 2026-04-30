const ss = SpreadsheetApp.getActiveSpreadsheet();

// *** แก้ URL นี้เป็น Replit URL จริงหลังได้ลิงก์ ***
const REPLIT_URL = 'https://frieght.sorravitsis.repl.co';

function doGet(e) {
  try {
    // External API mode — called by Replit frontend
    const action = (e.parameter.action || '').toLowerCase();
    if (action) {
      return ContentService
        .createTextOutput(JSON.stringify(routeApi(action)))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // Redirect browser to Replit UI (main web app)
    if (REPLIT_URL && !REPLIT_URL.includes('YOUR_REPLIT')) {
      return HtmlService.createHtmlOutput(
        '<script>window.location.replace("' + REPLIT_URL + '")</script>'
      ).setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
    }

    if (e.parameter.opt === 'getSummary') {
      return ContentService.createTextOutput(JSON.stringify(getSummaryData()))
        .setMimeType(ContentService.MimeType.JSON);
    }
    let role = e.parameter.keyword;
    if (role) {
      let filteredData1 = filterdata("ดรอปดาวน์")
      let filteredData2 = filterdata("บันทึกข้อมูล")

      let combinedData = {
        data1: filteredData1,
        data2: filteredData2,
      };

      let jsonData = JSON.stringify(combinedData);
      let jsonBlob = Utilities.newBlob(jsonData, 'application/json');
      let compressedBlob = Utilities.gzip(jsonBlob);
      let compressedBytes = compressedBlob.getBytes();
      let base64CompressedData = Utilities.base64Encode(compressedBytes);
      let response = ContentService.createTextOutput(base64CompressedData)
        .setMimeType(ContentService.MimeType.TEXT);
      return response;
    }
    return HtmlService.createTemplateFromFile('index').evaluate()
      .setTitle('Booking SolarPanel')
      .addMetaTag('viewport', 'width=device-width, initial-scale=1')
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ status: 'error', message: err.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/* สำหรับ google.script.run (ใช้แทน AJAX เพื่อหลีกเลี่ยง CORS/redirect issues) */
function getAllData() {
  try {
    Logger.log('getAllData called');
    let data1 = filterdataSafe("ดรอปดาวน์", 500);
    let data2 = filterdataSafe("บันทึกข้อมูล", 500);
    Logger.log('getAllData success: data1=' + data1.length + ' rows, data2=' + data2.length + ' rows');
    return { status: 'success', data1: data1, data2: data2 };
  } catch (e) {
    Logger.log('getAllData error: ' + e.message);
    return { status: 'error', message: e.message };
  }
}

function filterdataSafe(sheetname, maxRows) {
  let sheet = ss.getSheetByName(sheetname);
  if (!sheet) return [];
  let lastColumn = sheet.getLastColumn();
  let lastRow = sheet.getLastRow();
  if (lastRow < 2 || lastColumn < 1) return [];
  let dataValues = sheet.getRange(2, 1, Math.min(lastRow - 1, maxRows), lastColumn).getValues();
  return dataValues.filter(row => row[0] !== "").map(row => {
    return row.map(cell => {
      if (cell instanceof Error) return String(cell);
      if (cell instanceof Date) return Utilities.formatDate(cell, Session.getScriptTimeZone(), "yyyy-MM-dd'T'HH:mm:ss");
      return cell;
    });
  });
}

function getSummaryData() {
  const sheet = ss.getSheetByName('บันทึกข้อมูล');
  if (!sheet || sheet.getLastRow() < 2) return { status: 'success', count: 0, items: [] };

  const todayFmt = Utilities.formatDate(new Date(), 'GMT+7', 'yyyyMMdd');
  const rows = sheet.getRange(2, 1, sheet.getLastRow() - 1, 5).getValues();

  const items = rows
    .filter(row => {
      if (!row[0]) return false;
      const d = row[0] instanceof Date ? row[0] : new Date(row[0]);
      if (Number.isNaN(d.getTime())) return false;
      return Utilities.formatDate(d, 'GMT+7', 'yyyyMMdd') >= todayFmt;
    })
    .map(row => ({
      date: row[0] instanceof Date ? Utilities.formatDate(row[0], 'GMT+7', 'dd/MM/yyyy') : String(row[0]),
      name: String(row[1]),
      cartype: String(row[2]),
      amount: String(row[3]),
      location: String(row[4])
    }))
    .sort((a, b) => {
      const fmt = d => d.split('/').reverse().join('');
      return fmt(a.date).localeCompare(fmt(b.date));
    });

  return { status: 'success', count: items.length, items: items };
}

function routeApi(action) {
  switch (action) {
    case 'getalldata': return getAllData();
    case 'getsummary': return getSummaryData();
    case 'ping':       return { status: 'success', pong: true, time: new Date().toISOString() };
    default:           return { status: 'error', message: 'unknown action: ' + action };
  }
}

function ping() {
  return { status: 'success', pong: true, time: new Date().toISOString() };
}

function filterdata(sheetname, cols, condition = row => row[0] !== "") {
  let sheet = ss.getSheetByName(sheetname);
  let lastColumn = sheet.getLastColumn();
  let lastRow = sheet.getLastRow();

  if (lastRow < 2 || lastColumn < 1) {
    return [];
  }

  let chunkSize = 20000;
  let filteredRows = [];

  for (let startRow = 2; startRow <= lastRow; startRow += chunkSize) {
    let numRows = Math.min(chunkSize, lastRow - startRow + 1);
    let dataValues = sheet.getRange(startRow, 1, numRows, lastColumn).getValues();

    dataValues.forEach(row => {
      // ใช้เงื่อนไขที่ส่งเข้ามา (หรือค่าเริ่มต้น)ในการกรองข้อมูล
      if (condition(row)) {
        if (cols && Array.isArray(cols)) {
          let newRow = cols.map(col => row[col]);
          filteredRows.push(newRow);
        } else {
          filteredRows.push(row);
        }
      }
    });
  }

  return filteredRows;
}

function include(file) {
  return HtmlService.createHtmlOutputFromFile(file).getContent()
}

function getURL() {
  return ScriptApp.getService().getUrl();
}
