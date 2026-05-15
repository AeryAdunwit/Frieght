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
    workStatus: row.length >= 10 ? normalizeWorkStatus_(row[9]) : '',
    transportCompany: row.length >= 11 ? row[10] || '' : ''
  };
}

function getBookingAdminColumn_() {
  return 9;
}

function getBookingStatusColumn_() {
  return 10;
}

function getBookingTransportColumn_() {
  return 11;
}

function readTransportCompaniesFromSheet_() {
  const sheet = ss.getSheetByName('config');
  if (!sheet || sheet.getLastRow() < 1 || sheet.getLastColumn() < 3) return [];
  const rows = sheet.getRange(1, 3, sheet.getLastRow(), 1).getValues();
  const companies = [];
  const seen = new Set();
  rows.forEach(row => {
    const val = String(row[0] || '').trim();
    const key = val.toLowerCase();
    if (!val || key === 'ขนส่ง' || key === 'บริษัทขนส่ง' || key === 'transport') return;
    if (!seen.has(key)) {
      seen.add(key);
      companies.push(val);
    }
  });
  return companies;
}

function normalizeWorkStatus_(status) {
  const value = String(status || '').trim().toLowerCase();
  if (value === 'จบงานแล้ว' || value === 'completed' || value === 'complete' || value === 'done') {
    return 'completed';
  }
  if (value === 'ยกเลิก' || value === 'cancelled' || value === 'canceled' || value === 'cancel') {
    return 'cancelled';
  }
  return '';
}

function workStatusLabel_(status) {
  const normalized = normalizeWorkStatus_(status);
  if (normalized === 'completed') return 'จบงานแล้ว';
  if (normalized === 'cancelled') return 'ยกเลิก';
  return '';
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
    sheet.getRange(1, 1, 1, 13).setValues([[
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
      'ขนส่ง',
      'สถานะงาน'
    ]]);
    sheet.setFrozenRows(1);
    sheet.autoResizeColumns(1, 13);
  }

  return sheet;
}

function appendAdminCompletionLog_(booking, action) {
  const logSheet = ensureAdminLogSheet_();
  logSheet.appendRow([
    Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss'),
    action || 'จบงานแล้ว',
    booking.rowNumber,
    booking.adminName,
    booking.name,
    booking.date,
    booking.cartype,
    booking.product,
    booking.amount,
    booking.timeSlot,
    booking.location,
    booking.transportCompany || '',
    booking.workStatusLabel
  ]);
}

function parseBookingDateOnly_(value) {
  if (value instanceof Date && !Number.isNaN(value.getTime())) {
    return new Date(value.getFullYear(), value.getMonth(), value.getDate());
  }

  const text = String(value || '').trim();
  if (!text) return null;

  let match = text.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  if (match) {
    return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  }

  match = text.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/);
  if (match) {
    return new Date(Number(match[3]), Number(match[2]) - 1, Number(match[1]));
  }

  const parsed = new Date(text);
  if (Number.isNaN(parsed.getTime())) return null;
  return new Date(parsed.getFullYear(), parsed.getMonth(), parsed.getDate());
}

function startOfDay_(value) {
  const date = value instanceof Date ? value : new Date(value);
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function shouldAutoCompleteAssignedBooking_(booking, now) {
  if (!booking.adminName || booking.workStatus === 'completed' || booking.workStatus === 'cancelled') return false;

  const bookingDate = parseBookingDateOnly_(booking.date);
  if (!bookingDate) return false;

  const autoCompleteDate = new Date(bookingDate);
  autoCompleteDate.setDate(autoCompleteDate.getDate() + 1);

  return startOfDay_(now || new Date()).getTime() >= autoCompleteDate.getTime();
}

function autoCompleteAssignedBookings_(sheet) {
  if (!sheet || sheet.getLastRow() < 2) return 0;

  const width = Math.max(sheet.getLastColumn(), getBookingStatusColumn_());
  const rows = sheet.getRange(2, 1, sheet.getLastRow() - 1, width).getValues();
  const now = new Date();
  let completedCount = 0;

  rows.forEach((row, index) => {
    const rowNumber = index + 2;
    const booking = serializeBookingForAdmin_(row, rowNumber);
    if (!shouldAutoCompleteAssignedBooking_(booking, now)) return;

    sheet.getRange(rowNumber, getBookingStatusColumn_()).setValue('จบงานแล้ว');
    row[getBookingStatusColumn_() - 1] = 'จบงานแล้ว';
    const completedBooking = serializeBookingForAdmin_(row, rowNumber);
    appendAdminCompletionLog_(completedBooking, 'จบงานอัตโนมัติ');
    completedCount += 1;
  });

  return completedCount;
}

function ensureAdminConfigSheet_() {
  let sheet = ss.getSheetByName('config');
  if (!sheet) {
    sheet = ss.insertSheet('config');
  }

  if (sheet.getLastRow() < 1 || sheet.getLastColumn() < 1) {
    sheet.getRange(1, 1, 4, 2).setValues([
      ['ชื่อ', 'รหัส'],
      ['อุลัยพร', '0004'],
      ['วิไลวัลย์', '0567'],
      ['มนตรี', '0754']
    ]);
    sheet.autoResizeColumn(1);
    sheet.autoResizeColumn(2);
  }

  return sheet;
}

function readAdminUsersFromSheet_(sheet) {
  if (!sheet || sheet.getLastRow() < 1 || sheet.getLastColumn() < 1) return [];
  const rows = sheet.getRange(1, 1, sheet.getLastRow(), Math.min(sheet.getLastColumn(), 2)).getValues();
  const users = [];
  const seen = new Set();

  rows.forEach(row => {
    const firstCell = String(row[0] || '').trim();
    const secondCell = String(row[1] || '').trim();
    const firstKey = firstCell.toLowerCase();
    const secondKey = secondCell.toLowerCase();
    if (!firstCell || firstCell === 'ชื่อผู้รับเรื่อง' || firstKey === 'ชื่อ') return;
    if (firstKey === 'admin' || secondKey === 'ชื่อผู้รับเรื่อง' || secondKey === 'รหัส') return;

    const name = firstCell;
    const code = secondCell;
    const normalized = name.toLowerCase();
    if (name && code && !seen.has(normalized)) {
      seen.add(normalized);
      users.push({ name: name, code: code });
    }
  });

  return users;
}

function normalizeAdminCode_(code) {
  const value = String(code || '').trim();
  if (/^\d+$/.test(value)) return String(Number(value));
  return value.toLowerCase();
}

function readAdminNamesFromSheet_(sheet) {
  return readAdminUsersFromSheet_(sheet).map(user => user.name);
}

function getAdminUsers_() {
  const sheet = ensureAdminConfigSheet_();
  let users = readAdminUsersFromSheet_(sheet);

  if (!users.length) {
    const startRow = Math.max(sheet.getLastRow() + 1, 1);
    sheet.getRange(startRow, 1, 3, 2).setValues([
      ['อุลัยพร', '0004'],
      ['วิไลวัลย์', '0567'],
      ['มนตรี', '0754']
    ]);
    sheet.autoResizeColumn(1);
    sheet.autoResizeColumn(2);
    users = readAdminUsersFromSheet_(sheet);
  }

  return users;
}

function getAdminNames_() {
  return getAdminUsers_().map(user => user.name);
}

function verifyAdminCode_(code) {
  const cleanCode = String(code || '').trim();
  if (!cleanCode) throw new Error('กรุณากรอกรหัสพนักงาน Admin');

  const normalizedCode = normalizeAdminCode_(cleanCode);
  const user = getAdminUsers_().find(item => normalizeAdminCode_(item.code) === normalizedCode);
  if (!user) throw new Error('รหัสพนักงาน Admin ไม่ถูกต้อง');
  return user;
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
    workStatusLabel: workStatusLabel_(item.workStatus),
    transportCompany: String(item.transportCompany || '')
  };
}

function getAdminDashboardData(pin) {
  let lock = null;
  try {
    const currentAdmin = verifyAdminCode_(pin);
    const sheet = ss.getSheetByName('บันทึกข้อมูล');
    const admins = getAdminNames_();
    if (!sheet || sheet.getLastRow() < 2) {
      return { status: 'success', admins: admins, currentAdmin: currentAdmin, bookings: [] };
    }

    lock = LockService.getDocumentLock();
    if (!lock.tryLock(30000)) throw new Error('การล็อคคิวมีปัญหา โปรดลองใหม่อีกครั้ง');
    autoCompleteAssignedBookings_(sheet);
    lock.releaseLock();
    lock = null;

    const rows = sheet.getRange(2, 1, sheet.getLastRow() - 1, sheet.getLastColumn()).getValues();
    const bookings = rows
      .map((row, index) => serializeBookingForAdmin_(row, index + 2))
      .filter(item => item.date);

    return { status: 'success', admins: admins, currentAdmin: currentAdmin, bookings: bookings, transportCompanies: readTransportCompaniesFromSheet_() };
  } catch (e) {
    if (lock) lock.releaseLock();
    return { status: 'error', message: e.message };
  }
}

function assignBookingAdmin(pin, rowNumber, transportCompany) {
  let lock = null;
  try {
    const currentAdmin = verifyAdminCode_(pin);
    const sheet = ss.getSheetByName('บันทึกข้อมูล');
    if (!sheet) throw new Error('ไม่พบ Sheet ชื่อ บันทึกข้อมูล');

    const targetRow = Number(rowNumber);
    if (!Number.isInteger(targetRow) || targetRow < 2 || targetRow > sheet.getLastRow()) {
      throw new Error('ไม่พบรายการจองที่ต้องการอัปเดต');
    }

    lock = LockService.getDocumentLock();
    if (!lock.tryLock(30000)) throw new Error('การล็อคคิวมีปัญหา โปรดลองใหม่อีกครั้ง');
    sheet.getRange(targetRow, getBookingAdminColumn_()).setValue(currentAdmin.name);
    if (transportCompany) {
      sheet.getRange(targetRow, getBookingTransportColumn_()).setValue(String(transportCompany));
    }
    lock.releaseLock();
    lock = null;

    const width = Math.max(sheet.getLastColumn(), getBookingTransportColumn_());
    const row = sheet.getRange(targetRow, 1, 1, width).getValues()[0];
    return { status: 'success', booking: serializeBookingForAdmin_(row, targetRow) };
  } catch (e) {
    if (lock) lock.releaseLock();
    return { status: 'error', message: e.message };
  }
}

function completeBookingAdmin(pin, rowNumber) {
  let lock = null;
  try {
    verifyAdminCode_(pin);
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
    if (currentBooking.workStatus === 'cancelled') {
      throw new Error('รายการนี้ถูกยกเลิกแล้ว ไม่สามารถจบงานได้');
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

function cancelBookingAdmin(pin, rowNumber) {
  let lock = null;
  try {
    const currentAdmin = verifyAdminCode_(pin);
    const sheet = ss.getSheetByName('บันทึกข้อมูล');
    if (!sheet) throw new Error('ไม่พบ Sheet ชื่อ บันทึกข้อมูล');

    const targetRow = Number(rowNumber);
    if (!Number.isInteger(targetRow) || targetRow < 2 || targetRow > sheet.getLastRow()) {
      throw new Error('ไม่พบรายการจองที่ต้องการยกเลิก');
    }

    lock = LockService.getDocumentLock();
    if (!lock.tryLock(30000)) throw new Error('การล็อคคิวมีปัญหา โปรดลองใหม่อีกครั้ง');

    const width = Math.max(sheet.getLastColumn(), getBookingStatusColumn_());
    const row = sheet.getRange(targetRow, 1, 1, width).getValues()[0];
    const currentBooking = serializeBookingForAdmin_(row, targetRow);
    if (currentBooking.workStatus === 'completed') {
      throw new Error('รายการนี้จบงานแล้ว ไม่สามารถยกเลิกได้');
    }

    if (!currentBooking.adminName) {
      sheet.getRange(targetRow, getBookingAdminColumn_()).setValue(currentAdmin.name);
      row[getBookingAdminColumn_() - 1] = currentAdmin.name;
    }

    if (currentBooking.workStatus !== 'cancelled') {
      sheet.getRange(targetRow, getBookingStatusColumn_()).setValue('ยกเลิก');
      row[getBookingStatusColumn_() - 1] = 'ยกเลิก';
      const cancelledBooking = serializeBookingForAdmin_(row, targetRow);
      appendAdminCompletionLog_(cancelledBooking, 'ยกเลิก');
      lock.releaseLock();
      lock = null;
      return { status: 'success', booking: cancelledBooking };
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
      if (!(dFmt >= tFmt && dFmt <= eFmt)) return false;
      const ws = normalizeWorkStatus_(row[9] || '');
      return ws !== 'completed' && ws !== 'cancelled';
    })
    .map(row => {
      const item = bookingFromRow_(row);
      return {
        date:             item.date instanceof Date ? Utilities.formatDate(item.date, 'GMT+7', 'dd/MM/yyyy') : String(item.date),
        name:             String(item.name),
        cartype:          String(item.cartype),
        product:          String(item.product  || ''),
        amount:           String(item.amount),
        timeSlot:         String(item.timeSlot || ''),
        location:         String(item.location),
        adminName:        String(item.adminName        || ''),
        transportCompany: String(item.transportCompany || '')
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
