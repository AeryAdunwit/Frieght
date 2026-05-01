const ss = SpreadsheetApp.getActiveSpreadsheet();

function doGet(e) {
  try {
    // External API mode
    const action = (e.parameter.action || '').toLowerCase();
    if (action) {
      return ContentService
        .createTextOutput(JSON.stringify(routeApi(action)))
        .setMimeType(ContentService.MimeType.JSON);
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
  const rows = sheet.getRange(2, 1, sheet.getLastRow() - 1, sheet.getLastColumn()).getValues();

  const items = rows
    .filter(row => {
      if (!row[0]) return false;
      const d = row[0] instanceof Date ? row[0] : new Date(row[0]);
      if (Number.isNaN(d.getTime())) return false;
      return Utilities.formatDate(d, 'GMT+7', 'yyyyMMdd') >= todayFmt;
    })
    .map(row => {
      const item = bookingFromRow_(row);
      return {
        date: item.date instanceof Date ? Utilities.formatDate(item.date, 'GMT+7', 'dd/MM/yyyy') : String(item.date),
        name: String(item.name),
        cartype: String(item.cartype),
        product: String(item.product || ''),
        amount: String(item.amount),
        timeSlot: String(item.timeSlot || ''),
        location: String(item.location),
        adminName: String(item.adminName || '')
      };
    })
    .sort((a, b) => {
      const fmt = d => d.split('/').reverse().join('');
      return fmt(a.date).localeCompare(fmt(b.date));
    });

  return { status: 'success', count: items.length, items: items };
}

function bookingFromRow_(row) {
  const isExpanded = row.length >= 7;
  return {
    date: row[0],
    name: row[1],
    cartype: row[2],
    product: isExpanded ? row[3] : '',
    amount: isExpanded ? row[4] : row[3],
    timeSlot: isExpanded ? row[5] : '',
    location: isExpanded ? row[6] : row[4],
    adminName: row.length >= 9 ? row[8] || '' : '',
    workStatus: row.length >= 10 ? normalizeWorkStatus_(row[9]) : ''
  };
}

function getAdminPin_() {
  return PropertiesService.getScriptProperties().getProperty('ADMIN_PIN') || '';
}

function verifyAdminPin_(pin) {
  const expected = getAdminPin_();
  if (!expected) throw new Error('ยังไม่ได้ตั้งค่า ADMIN_PIN ใน Script Properties');
  if (String(pin || '') !== expected) throw new Error('รหัส Admin ไม่ถูกต้อง');
}

function getBookingAdminColumn_() {
  return 9;
}

function getBookingStatusColumn_() {
  return 10;
}

function normalizeWorkStatus_(status) {
  const value = String(status || '').trim().toLowerCase();
  if (value === 'จบงานแล้ว' || value === 'completed' || value === 'complete' || value === 'done') {
    return 'completed';
  }
  return '';
}

function workStatusLabel_(status) {
  return normalizeWorkStatus_(status) === 'completed' ? 'จบงานแล้ว' : '';
}

function formatCellValue_(cell) {
  if (cell instanceof Error) return String(cell);
  if (cell instanceof Date) return Utilities.formatDate(cell, Session.getScriptTimeZone(), "yyyy-MM-dd'T'HH:mm:ss");
  return cell == null ? '' : cell;
}

function ensureAdminLogSheet_() {
  let sheet = ss.getSheetByName('admin_log');
  if (!sheet) {
    sheet = ss.insertSheet('admin_log');
  }

  if (sheet.getLastRow() < 1) {
    sheet.getRange(1, 1, 1, 12).setValues([[
      'เวลาบันทึก',
      'action',
      'booking_row',
      'admin',
      'ชื่อผู้จอง',
      'วันที่จอง',
      'ประเภทรถ',
      'สินค้า',
      'จำนวน',
      'ช่วงเวลา',
      'จังหวัด',
      'สถานะงาน'
    ]]);
    sheet.setFrozenRows(1);
    sheet.autoResizeColumns(1, 12);
  }

  return sheet;
}

function appendAdminCompletionLog_(booking) {
  const logSheet = ensureAdminLogSheet_();
  logSheet.appendRow([
    Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss'),
    'จบงานแล้ว',
    booking.rowNumber,
    booking.adminName,
    booking.name,
    booking.date,
    booking.cartype,
    booking.product,
    booking.amount,
    booking.timeSlot,
    booking.location,
    booking.workStatusLabel
  ]);
}

function ensureAdminConfigSheet_() {
  let sheet = ss.getSheetByName('config');
  if (!sheet) {
    sheet = ss.insertSheet('config');
  }

  if (sheet.getLastRow() < 1 || sheet.getLastColumn() < 1) {
    sheet.getRange(1, 1, 3, 1).setValues([
      ['โก้'],
      ['กี้'],
      ['กุ๊ก']
    ]);
    sheet.autoResizeColumn(1);
  }

  return sheet;
}

function readAdminNamesFromSheet_(sheet) {
  if (!sheet || sheet.getLastRow() < 1 || sheet.getLastColumn() < 1) return [];
  const rows = sheet.getRange(1, 1, sheet.getLastRow(), Math.min(sheet.getLastColumn(), 2)).getValues();
  const names = [];
  const seen = new Set();

  rows.forEach(row => {
    const firstCell = String(row[0] || '').trim();
    const secondCell = String(row[1] || '').trim();
    const key = firstCell.toLowerCase();
    const name = key === 'admin' ? secondCell : firstCell;
    const normalized = name.toLowerCase();
    if (name && name !== 'ชื่อผู้รับเรื่อง' && normalized !== 'admin' && !seen.has(normalized)) {
      seen.add(normalized);
      names.push(name);
    }
  });

  return names;
}

function getAdminNames_() {
  const sheet = ensureAdminConfigSheet_();
  let names = readAdminNamesFromSheet_(sheet);

  if (!names.length) {
    const startRow = Math.max(sheet.getLastRow() + 1, 1);
    sheet.getRange(startRow, 1, 3, 1).setValues([
      ['โก้'],
      ['กี้'],
      ['กุ๊ก']
    ]);
    sheet.autoResizeColumn(1);
    names = readAdminNamesFromSheet_(sheet);
  }

  return names;
}

function serializeBookingForAdmin_(row, rowNumber) {
  const item = bookingFromRow_(row);
  return {
    rowNumber: rowNumber,
    date: formatCellValue_(item.date),
    name: String(item.name || ''),
    cartype: String(item.cartype || ''),
    product: String(item.product || ''),
    amount: String(item.amount || ''),
    timeSlot: String(item.timeSlot || ''),
    location: String(item.location || ''),
    adminName: String(item.adminName || ''),
    workStatus: String(item.workStatus || ''),
    workStatusLabel: workStatusLabel_(item.workStatus)
  };
}

function getAdminDashboardData(pin) {
  try {
    verifyAdminPin_(pin);
    const sheet = ss.getSheetByName('บันทึกข้อมูล');
    const admins = getAdminNames_();
    if (!sheet || sheet.getLastRow() < 2) {
      return { status: 'success', admins: admins, bookings: [] };
    }

    const rows = sheet.getRange(2, 1, sheet.getLastRow() - 1, sheet.getLastColumn()).getValues();
    const bookings = rows
      .map((row, index) => serializeBookingForAdmin_(row, index + 2))
      .filter(item => item.date);

    return { status: 'success', admins: admins, bookings: bookings };
  } catch (e) {
    return { status: 'error', message: e.message };
  }
}

function assignBookingAdmin(pin, rowNumber, adminName) {
  let lock = null;
  try {
    verifyAdminPin_(pin);
    const sheet = ss.getSheetByName('บันทึกข้อมูล');
    if (!sheet) throw new Error('ไม่พบ Sheet ชื่อ บันทึกข้อมูล');

    const targetRow = Number(rowNumber);
    if (!Number.isInteger(targetRow) || targetRow < 2 || targetRow > sheet.getLastRow()) {
      throw new Error('ไม่พบรายการจองที่ต้องการอัปเดต');
    }

    const cleanAdminName = String(adminName || '').trim();
    const admins = getAdminNames_();
    if (cleanAdminName && admins.indexOf(cleanAdminName) === -1) {
      throw new Error('ไม่พบรายชื่อผู้รับเรื่องใน config');
    }

    lock = LockService.getDocumentLock();
    if (!lock.tryLock(30000)) throw new Error('การล็อคคิวมีปัญหา โปรดลองใหม่อีกครั้ง');
    sheet.getRange(targetRow, getBookingAdminColumn_()).setValue(cleanAdminName);
    lock.releaseLock();
    lock = null;

    const row = sheet.getRange(targetRow, 1, 1, Math.max(sheet.getLastColumn(), getBookingAdminColumn_())).getValues()[0];
    return { status: 'success', booking: serializeBookingForAdmin_(row, targetRow) };
  } catch (e) {
    if (lock) lock.releaseLock();
    return { status: 'error', message: e.message };
  }
}

function completeBookingAdmin(pin, rowNumber) {
  let lock = null;
  try {
    verifyAdminPin_(pin);
    const sheet = ss.getSheetByName('บันทึกข้อมูล');
    if (!sheet) throw new Error('ไม่พบ Sheet ชื่อ บันทึกข้อมูล');

    const targetRow = Number(rowNumber);
    if (!Number.isInteger(targetRow) || targetRow < 2 || targetRow > sheet.getLastRow()) {
      throw new Error('ไม่พบรายการจองที่ต้องการจบงาน');
    }

    lock = LockService.getDocumentLock();
    if (!lock.tryLock(30000)) throw new Error('การล็อคคิวมีปัญหา โปรดลองใหม่อีกครั้ง');

    const width = Math.max(sheet.getLastColumn(), getBookingStatusColumn_());
    const row = sheet.getRange(targetRow, 1, 1, width).getValues()[0];
    const currentBooking = serializeBookingForAdmin_(row, targetRow);
    if (!currentBooking.adminName) {
      throw new Error('ต้องเลือกผู้รับเรื่องก่อนจบงาน');
    }

    if (currentBooking.workStatus !== 'completed') {
      sheet.getRange(targetRow, getBookingStatusColumn_()).setValue('จบงานแล้ว');
      row[getBookingStatusColumn_() - 1] = 'จบงานแล้ว';
      const completedBooking = serializeBookingForAdmin_(row, targetRow);
      appendAdminCompletionLog_(completedBooking);
      lock.releaseLock();
      lock = null;
      return { status: 'success', booking: completedBooking };
    }

    lock.releaseLock();
    lock = null;
    return { status: 'success', booking: currentBooking };
  } catch (e) {
    if (lock) lock.releaseLock();
    return { status: 'error', message: e.message };
  }
}

function routeApi(action) {
  switch (action) {
    case 'getalldata':        return getAllData();
    case 'getsummary':        return getSummaryData();
    case 'getupcomingsummary': return getUpcomingSummaryData();
    case 'ping':              return { status: 'success', pong: true, time: new Date().toISOString() };
    default:                  return { status: 'error', message: 'unknown action: ' + action };
  }
}

function getUpcomingSummaryData() {
  const sheet = ss.getSheetByName('บันทึกข้อมูล');
  if (!sheet || sheet.getLastRow() < 2) return { status: 'success', count: 0, items: [] };

  const now = new Date();
  const tomorrow = new Date(now);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const endDay = new Date(tomorrow);
  endDay.setDate(endDay.getDate() + 3);

  const tFmt = Utilities.formatDate(tomorrow, 'GMT+7', 'yyyyMMdd');
  const eFmt = Utilities.formatDate(endDay,   'GMT+7', 'yyyyMMdd');

  const rows = sheet.getRange(2, 1, sheet.getLastRow() - 1, sheet.getLastColumn()).getValues();

  const items = rows
    .filter(row => {
      if (!row[0]) return false;
      const d = row[0] instanceof Date ? row[0] : new Date(row[0]);
      if (Number.isNaN(d.getTime())) return false;
      const dFmt = Utilities.formatDate(d, 'GMT+7', 'yyyyMMdd');
      return dFmt >= tFmt && dFmt <= eFmt;
    })
    .map(row => {
      const item = bookingFromRow_(row);
      return {
        date:     item.date instanceof Date ? Utilities.formatDate(item.date, 'GMT+7', 'dd/MM/yyyy') : String(item.date),
        name:     String(item.name),
        cartype:  String(item.cartype),
        product:  String(item.product  || ''),
        amount:   String(item.amount),
        timeSlot: String(item.timeSlot || ''),
        location: String(item.location)
      };
    })
    .sort((a, b) => {
      const fmt = d => d.split('/').reverse().join('');
      return fmt(a.date).localeCompare(fmt(b.date));
    });

  return { status: 'success', count: items.length, items: items };
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
