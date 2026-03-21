(function attachFreightChatRenderers(global) {
  function escapeAttr(text) {
    return String(text || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function renderBookingFollowupHtml() {
    return `
      <p style="margin-bottom: 10px;">อยากได้สรุปขั้นตอนต่อไหมค้าบ</p>
      <div style="display: flex; gap: 10px;">
        <button class="quick-btn" style="flex:1; text-align:center; justify-content:center;" onclick="handleBookingFollowup(true)">สรุปขั้นตอน</button>
        <button class="quick-btn" style="flex:1; text-align:center; justify-content:center;" onclick="handleBookingFollowup(false)">ไว้ก่อนน้า</button>
      </div>
    `;
  }

  function renderHandoffSummaryHtml(chips, note) {
    const chipHtml = Array.isArray(chips) && chips.length
      ? `<div class="handoff-summary-list">${chips.map((chip) => `<span class="handoff-summary-chip">${escapeAttr(chip)}</span>`).join('')}</div>`
      : '';
    return `
      <div class="handoff-summary-title">ข้อมูลที่น้องจับได้จากแชตนี้</div>
      ${chipHtml}
      <div class="handoff-summary-note">${escapeAttr(note)}</div>
    `;
  }

  function renderIntakeCoachHtml({ title, line, ready, chips }) {
    const chipHtml = Array.isArray(chips) && chips.length
      ? `<div class="chat-intake-list">${chips.map((chip) => `<span class="chat-intake-chip">${escapeAttr(chip)}</span>`).join('')}</div>`
      : '';
    return `
      <div class="chat-intake-head">
        <div class="chat-intake-title">${escapeAttr(title || 'เช็กข้อมูลงาน')}</div>
        <span class="chat-intake-badge ${ready ? 'ready' : ''}">${ready ? 'พร้อมส่งต่อ' : 'ยังไม่ครบ'}</span>
      </div>
      <div class="chat-intake-line">${escapeAttr(line || '')}</div>
      ${chipHtml}
    `;
  }

  global.FreightChatRenderers = Object.freeze({
    renderBookingFollowupHtml,
    renderHandoffSummaryHtml,
    renderIntakeCoachHtml
  });
})(window);
