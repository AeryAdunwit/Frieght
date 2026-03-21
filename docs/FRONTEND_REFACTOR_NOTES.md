# Frontend Refactor Notes

รอบนี้แยกก้อนที่ปลอดภัยก่อน โดยไม่กระทบหน้าเว็บปัจจุบัน

## สิ่งที่แยกออกแล้ว
- `Frieght/js/chat-runtime.js`
  - meta config reader
  - API base URL resolver
  - public site base URL resolver
  - frontend error buffer
  - session state load/save
  - aria live announcer

## สิ่งที่ยังคงเดิม
- `Frieght/js/chat.js` ยังเป็น entrypoint เดิม
- `Frieght/index.html` ยังโหลดหน้าเดิมและ DOM เดิม
- ไม่มี build step ใหม่
- ไม่เปลี่ยน route หรือ API contract

## เป้าหมายรอบถัดไป
- แยก `topic suggestions / intake coach / handoff UI` ออกจาก `chat.js`
- แยก DOM binding ออกจาก business logic
- ค่อยพิจารณา move ไป framework เมื่อพร้อมจริง
