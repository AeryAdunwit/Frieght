function doPost(e) {
  let { opt } = e.parameter;
  let actions = {
    savecar: savecars,
  };
  return actions[opt] ? actions[opt](e.parameter) : ContentService.createTextOutput(
    JSON.stringify({ status: 'error', message: 'Invalid opt parameter' })
  ).setMimeType(ContentService.MimeType.JSON);
}

let time = Utilities.formatDate(new Date(), "GMT+7", "dd/MM/yyyy HH:mm:ss")

function savecars(val) {
  try {
    let { date, name, cartype, amount, location } = val;
    if (!ss) {
      return ContentService.createTextOutput(JSON.stringify({ status: 'error', message: 'ไม่พบ Spreadsheet (ss ไม่ได้ถูกกำหนด)' }))
        .setMimeType(ContentService.MimeType.JSON)
    }
    let sheet = ss.getSheetByName('บันทึกข้อมูล')
    if (!sheet) {
      return ContentService.createTextOutput(JSON.stringify({ status: 'error', message: 'ไม่พบ Sheet ชื่อ บันทึกข้อมูล' }))
        .setMimeType(ContentService.MimeType.JSON)
    }
    let lock = LockService.getDocumentLock()
    if (!lock.tryLock(30000)) {
      return ContentService.createTextOutput(JSON.stringify({ status: 'error', message: 'การล็อคคิวมีปัญหา โปรดบันทึกใหม่อีกครั้ง' }))
        .setMimeType(ContentService.MimeType.JSON)
    }
    let info = [date, name, cartype, amount, location, time]
    sheet.appendRow(info)
    lock.releaseLock()
    return ContentService.createTextOutput(JSON.stringify({ status: 'success', message: "บันทึกการจองเรียบร้อย" }))
      .setMimeType(ContentService.MimeType.JSON)
  } catch (e) {
    return ContentService.createTextOutput(JSON.stringify({ status: 'error', message: e.message }))
      .setMimeType(ContentService.MimeType.JSON)
  }
}