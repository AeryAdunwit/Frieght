(function attachFreightChatContent(global) {
  const TOPIC_COMPOSER_HINTS = {
    general: {
      placeholder: 'พิมพ์คำถามที่นี่...',
      hint: 'พิมพ์ตรง ๆ มาได้เลยค้าบ น้องโกดังช่วยจับประเด็นให้'
    },
    pricing: {
      placeholder: 'เช่น ต้นทาง กรุงเทพ ปลายทาง ชลบุรี สินค้า 3 พาเลท',
      hint: '<strong>คำนวณค่าส่ง:</strong> พิมพ์ต้นทาง ปลายทาง ประเภทสินค้า และจำนวนมาได้เลยค้าบ'
    },
    booking: {
      placeholder: 'เช่น รับของจาก บางนา ไป ลำลูกกา ของ 10 ลัง พรุ่งนี้บ่าย',
      hint: '<strong>จองส่งสินค้า:</strong> พิมพ์ต้นทาง ปลายทาง ประเภทสินค้า จำนวน และช่วงเวลาที่อยากเข้ารับค้าบ'
    },
    claim: {
      placeholder: 'เช่น สินค้าชำรุด DO 1314639771 มีรูปครบแล้ว',
      hint: '<strong>เคลม / แจ้งปัญหา:</strong> พิมพ์เลข DO อาการปัญหา และหลักฐานที่มีมาได้เลยค้าบ'
    },
    coverage: {
      placeholder: 'เช่น ส่งไปต่างจังหวัดได้ไหม หรือมีพื้นที่ไหนต้องเช็กก่อน',
      hint: '<strong>พื้นที่บริการ:</strong> ถามเรื่องส่งต่างจังหวัด พื้นที่พิเศษ หรือจังหวัดปลายทางได้เลยค้าบ'
    },
    documents: {
      placeholder: 'เช่น ต้องใช้เอกสารอะไรบ้างสำหรับการส่ง',
      hint: '<strong>เอกสาร:</strong> ถามตรง ๆ ได้เลยว่าต้องใช้เอกสารอะไรบ้างค้าบ'
    },
    timeline: {
      placeholder: 'เช่น ปกติส่งกี่วัน หรือ ตัดรอบกี่โมง',
      hint: '<strong>ระยะเวลา:</strong> ถามเรื่องวันส่ง ตัดรอบ หรืออะไรที่ทำให้ช้าได้เลยค้าบ'
    },
    tracking: {
      placeholder: 'เช่น 1314639771',
      hint: '<strong>ติดตามพัสดุ:</strong> ส่งเลข DO มาได้เลย เดี๋ยวน้องเช็กให้ค้าบ'
    },
    solar: {
      placeholder: 'เช่น งาน Solar จาก อยุธยา ไป ขอนแก่น 48 แผง ส่งสัปดาห์หน้า',
      hint: '<strong>ส่ง Solar ผ่าน Hub:</strong> พิมพ์ต้นทาง ปลายทาง จำนวนแผง รุ่นสินค้า และวันส่งได้เลยค้าบ'
    },
    handoff: {
      placeholder: 'พิมพ์สรุปสั้น ๆ ให้ทีมได้เลยค้าบ',
      hint: ''
    }
  };

  const RESPONSE_MODE_LABELS = {
    quick: 'ตอบสั้น ตรงประเด็น',
    detail: 'ตอบครบขึ้นอีกนิด อ่านง่าย'
  };

  const TOPIC_SUGGESTIONS = {
    general: [],
    pricing: [
      { label: 'กทม. → ขอนแก่น', text: 'ส่งของจาก กรุงเทพ ไป ขอนแก่น ราคาเท่าไหร่' },
      { label: 'สินค้า 3 พาเลท', text: 'สินค้า 3 พาเลท ช่วยประเมินราคาให้หน่อย' }
    ],
    booking: [
      { label: 'รับของพรุ่งนี้เช้า', text: 'อยากจองรถไปรับของพรุ่งนี้เช้า' },
      { label: 'รถใหญ่ / เหมาคัน', text: 'งานรถใหญ่หรือเหมาคันต้องใช้ข้อมูลอะไรบ้าง' }
    ],
    claim: [
      { label: 'สินค้าชำรุด', text: 'สินค้าชำรุดต้องทำยังไง' },
      { label: 'ต้องใช้หลักฐานอะไร', text: 'เคลมต้องใช้หลักฐานอะไรบ้าง' }
    ],
    coverage: [
      { label: 'ส่งต่างจังหวัดไหม', text: 'ส่งต่างจังหวัดได้ไหม' },
      { label: 'พื้นที่ต้องเช็กก่อน', text: 'มีพื้นที่ไหนที่ต้องเช็กก่อนบ้าง' }
    ],
    documents: [
      { label: 'ต้องใช้เอกสารอะไร', text: 'ต้องใช้เอกสารอะไรบ้าง' },
      { label: 'ถ้าเอกสารไม่ครบ', text: 'ถ้าเอกสารไม่ครบต้องทำยังไง' }
    ],
    timeline: [
      { label: 'ปกติใช้กี่วัน', text: 'ปกติใช้เวลากี่วัน' },
      { label: 'ตัดรอบกี่โมง', text: 'ตัดรอบกี่โมง' }
    ],
    tracking: [
      { label: 'พิมพ์เลข DO', text: '1314639771' },
      { label: 'ไม่เจอข้อมูลทำไง', text: 'ถ้าไม่เจอข้อมูลต้องทำยังไง' }
    ],
    solar: [
      { label: 'ส่ง Solar ไปขอนแก่น', text: 'ส่ง solar ไป ขอนแก่น ราคาเท่าไหร่' },
      { label: 'ต้องเตรียมอะไรบ้าง', text: 'ส่ง Solar ผ่าน Hub ต้องเตรียมข้อมูลอะไรบ้าง' },
      { label: 'ข้อจำกัด Solar', text: 'ข้อจำกัด solar hub มีอะไรบ้าง' }
    ],
    handoff: []
  };

  function renderWelcomeCardHtml() {
    return `
      <div id="welcome-card" style="padding: 12px;">
        <div style="background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin-bottom: 12px;">
          <p style="margin: 0 0 6px; font-weight: 700; color: var(--primary);">น้องโกดังพร้อมให้บริการรรร</p>
          <p style="margin: 0; font-size: 13px; color: var(--gray);">เลือกหัวข้อได้เลย หรือพิมพ์ตรง ๆ มา น้องโกดังจะช่วยตอบให้ค้าบ</p>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
          <button class="quick-btn" onclick="handleCalculateAction()">📦 คำนวณค่าส่ง(ยังไม่เปิดให้บริการ)</button>
          <button class="quick-btn" onclick="handleBookingAction()">🚚 จองส่งสินค้า เหมาคัน/ขนาดใหญ่</button>
          <button class="quick-btn" onclick="quickAsk('วิธีติดตามสถานะพัสดุ')">🔍 ติดตามพัสดุ</button>
          <button class="quick-btn" onclick="handleSolarHubAction()">🏭 ส่ง Solar ผ่าน Hub</button>
          <button class="quick-btn" onclick="handleOtherInquiry()" style="grid-column: span 2;">💬 อื่นๆ (สอบถามเพิ่มเติม)</button>
        </div>
      </div>
    `;
  }

  global.FreightChatContent = Object.freeze({
    TOPIC_COMPOSER_HINTS,
    RESPONSE_MODE_LABELS,
    TOPIC_SUGGESTIONS,
    renderWelcomeCardHtml
  });
})(window);
