const ss = SpreadsheetApp.getActiveSpreadsheet();

function doGet(e) {
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
