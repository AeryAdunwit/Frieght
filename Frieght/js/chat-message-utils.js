(function attachFreightChatMessageUtils(global) {
  function isLikelyTrackingCode(text) {
    return /\d+/.test(text || '');
  }

  function escapeHtml(text) {
    return (text || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function stripInternalSystemData(text) {
    let normalized = String(text || '');
    normalized = normalized.replace(/```json[\s\S]*?```/gi, '');
    normalized = normalized.replace(/\[SYSTEM DATA\][\s\S]*?(?=\n{2,}|$)/gi, '');
    normalized = normalized.replace(/\[SYSTEM DATA:[^\]]*\]/gi, '');
    normalized = normalized.replace(/^\s*json\s*\{.*$/gim, '');
    normalized = normalized.replace(/^\s*[\{\[].*(tracking_results|estimated_delivery|out for delivery|details).*$\n?/gim, '');
    normalized = normalized.replace(/\n{3,}/g, '\n\n').trim();
    return normalized || String(text || '');
  }

  function sanitizeUrl(url) {
    if (!url) return '';
    try {
      const parsed = new URL(url);
      return /^https?:$/i.test(parsed.protocol) ? parsed.href : '';
    } catch (error) {
      return '';
    }
  }

  function renderSafeTextHtml(text) {
    const source = stripInternalSystemData(text || '');
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const parts = source.split(urlRegex);
    return parts.map((part, index) => {
      if (index % 2 === 1) {
        const safeUrl = sanitizeUrl(part);
        if (!safeUrl) {
          return escapeHtml(part);
        }
        const escapedUrl = escapeHtml(safeUrl);
        return `<a href="${escapedUrl}" target="_blank" rel="noopener noreferrer" style="color: inherit; text-decoration: underline; font-weight: bold;">${escapedUrl}</a>`;
      }
      return escapeHtml(part);
    }).join('').replace(/\n/g, '<br>');
  }

  function getTrackingSmallTalkReply(text) {
    const normalized = (text || '').trim().toLowerCase();
    if (!normalized || isLikelyTrackingCode(normalized)) return null;

    const patterns = [
      { test: /(hi|hello|หวัดดี|สวัสดี|ดีจ้า|ดีครับ|ดีคับ)/i, reply: 'สวัสดีค้าบ จะคุยเล่นก่อน หรือส่ง DO มาให้เช็กเลยก็ได้' },
      { test: /(ขอบคุณ|thank|thx|thanks)/i, reply: 'ยินดีค้าบ มี DO ต่อก็ส่งมาได้เลย หรือจะคุยเล่นรอผลก็ได้' },
      { test: /(หิว|เหนื่อย|ง่วง|เหงา|เบื่อ|เครียด|ท้อ|เศร้า)/i, reply: 'โอ๋เอ๋ก่อนค้าบ เหนื่อยก็พักได้ เดี๋ยวค่อยส่ง DO มา น้องช่วยต่อให้' },
      { test: /(ชื่ออะไร|ชื่อไร|ใคร|เป็นใคร)/i, reply: 'น้องโกดังค้าบ เช็กพัสดุก็ได้ คุยเล่นก็ไหว' },
      { test: /(ทำอะไรได้|ช่วยอะไรได้|ทำไรได้)/i, reply: 'น้องช่วยเช็กพัสดุ ตอบเรื่องบริการ และคุยเล่นได้ค้าบ' },
      { test: /(555|ฮ่า|ตลก|มุก|ขำ)/i, reply: 'มุกวันนี้คือ ของอาจยังไม่ถึง แต่เดดไลน์ถึงก่อนค้าบ หายขำแล้วส่ง DO มาได้เลย' },
      { test: /(ฝันดี|good night|gn|นอนก่อน)/i, reply: 'ฝันดีค้าบ ตื่นมาแล้วค่อยทักน้องใหม่ได้เสมอ' },
      { test: /(รักนะ|คิดถึง|miss you|love you)/i, reply: 'เขินค้าบ แต่ยังทำงานไหวนะ ส่ง DO มาได้เลยถ้าจะให้ช่วยต่อ' },
      { test: /(กินข้าว|กินอะไร|ข้าวยัง)/i, reply: 'น้องกินข้อมูลแทนข้าวค้าบ แต่คุณอย่าลืมกินข้าวนะ แล้วค่อยส่ง DO มาให้น้อง' },
      { test: /(อยู่ไหม|ว่างไหม|คุยได้ไหม|อยู่รึเปล่า)/i, reply: 'อยู่ค้าบ จะคุยเล่นหรือส่ง DO มาให้น้องเช็คก็ได้' }
    ];

    for (const item of patterns) {
      if (item.test.test(normalized)) return item.reply;
    }

    if (normalized.length <= 80) {
      return 'คุยได้ค้าบ น้องพร้อมฟัง แต่ถ้าจะเช็กพัสดุไว ๆ ส่ง DO มาได้เลย';
    }
    return null;
  }

  function extractTrackingLinkData(text, publicToolLinks) {
    if (!text) return null;
    const urlMatch = text.match(/https?:\/\/[^\s]+/);
    if (!urlMatch) return null;

    const trackingUrl = sanitizeUrl(urlMatch[0]);
    if (!trackingUrl) return null;
    const isSkyfrog = trackingUrl.includes(publicToolLinks?.skyfrog || '');
    const isSkyfrogSearch = trackingUrl.includes('track.skyfrog.net');
    const isPorlor = trackingUrl.includes('rfe.co.th') || trackingUrl.includes('porlor-tracking.html');

    return {
      trackingUrl,
      isSkyfrog: isSkyfrog || isSkyfrogSearch,
      isSkyfrogSearch,
      isPorlor,
      summary: escapeHtml(text.replace(trackingUrl, '').trim()).replace(/\n/g, '<br>')
    };
  }

  function openTrackingRedirect(url) {
    const safeUrl = sanitizeUrl(url);
    if (!safeUrl) return;
    try {
      window.open(safeUrl, '_blank', 'noopener,noreferrer');
    } catch (error) {
      console.warn('Unable to open tracking link in a new tab:', error);
    }
  }

  function renderTrackingCard(text, publicToolLinks) {
    const trackingData = extractTrackingLinkData(text, publicToolLinks);
    if (!trackingData) return null;

    const { trackingUrl, summary, isSkyfrog, isPorlor } = trackingData;
    if (isSkyfrog && !isPorlor) {
      return `
        <div style="display:flex; flex-direction:column; gap:10px;">
          <div>${summary}</div>
          <div style="border:1px solid var(--border); border-radius:14px; overflow:hidden; background:linear-gradient(135deg, rgba(233, 30, 52, 0.08), rgba(255,255,255,0.98));">
            <div style="padding:12px 14px; font-weight:700; color:var(--primary);">เปิด Skyfrog ในแท็บใหม่ได้เลยค้าบ</div>
            <div style="padding:0 14px 14px; color:var(--gray); font-size:13px; line-height:1.5;">น้องโกดังผูกลิงก์ค้นหาสถานะไว้ให้แล้ว กดเปิดในแท็บใหม่ได้เลยค้าบ</div>
            <div style="padding:0 14px 14px; display:flex; gap:10px; flex-wrap:wrap;">
              <a href="${trackingUrl}" target="_blank" rel="noopener noreferrer" style="display:inline-block; border:1px solid var(--primary); color:var(--primary); padding:10px 14px; border-radius:10px; text-decoration:none; font-weight:700;">เปิด Skyfrog ในแท็บใหม่</a>
            </div>
          </div>
        </div>
      `;
    }

    if (isPorlor) {
      return `
        <div style="display:flex; flex-direction:column; gap:10px;">
          <div>${summary}</div>
          <div style="border:1px solid var(--border); border-radius:14px; overflow:hidden; background:linear-gradient(135deg, rgba(233, 30, 52, 0.08), rgba(255,255,255,0.98));">
            <div style="padding:12px 14px; font-weight:700; color:var(--primary);">เปิดหน้าเช็ค Porlor ในแท็บใหม่ได้เลยค้าบ</div>
            <div style="padding:0 14px 14px; color:var(--gray); font-size:13px; line-height:1.5;">น้องโกดังแปะลิงก์หน้าเช็คของ Porlor ไว้ให้แล้ว กดเปิดต่อได้เลยค้าบ</div>
            <div style="padding:0 14px 14px; display:flex; gap:10px; flex-wrap:wrap;">
              <a href="${trackingUrl}" target="_blank" rel="noopener noreferrer" style="display:inline-block; border:1px solid var(--primary); color:var(--primary); padding:10px 14px; border-radius:10px; text-decoration:none; font-weight:700;">เปิด Porlor ในแท็บใหม่</a>
            </div>
          </div>
        </div>
      `;
    }

    return `
      <div style="display:flex; flex-direction:column; gap:10px;">
        <div>${summary}</div>
        <div style="border:1px solid var(--border); border-radius:14px; overflow:hidden; background:linear-gradient(135deg, rgba(233, 30, 52, 0.08), rgba(255,255,255,0.98));">
          <div style="padding:12px 14px; font-weight:700; color:var(--primary);">เปิดหน้าเช็คสถานะในแท็บใหม่ได้เลยค้าบ</div>
          <div style="padding:0 14px 14px; color:var(--gray); font-size:13px; line-height:1.5;">น้องโกดังแปะลิงก์เว็บขนส่งไว้ให้แล้ว กดเปิดในแท็บใหม่ได้เลยค้าบ</div>
          <div style="padding:0 14px 14px; display:flex; gap:10px; flex-wrap:wrap;">
            <a href="${trackingUrl}" target="_blank" rel="noopener noreferrer" style="display:inline-block; border:1px solid var(--primary); color:var(--primary); padding:10px 14px; border-radius:10px; text-decoration:none; font-weight:700;">เปิดลิงก์ในแท็บใหม่</a>
          </div>
        </div>
      </div>
    `;
  }

  function createFeedbackActions({ userText, botText, apiUrl, chatSessionId, visitorId }) {
    const actions = document.createElement('div');
    actions.className = 'feedback-actions';
    actions.style.display = 'flex';
    actions.style.gap = '8px';
    actions.style.flexWrap = 'wrap';

    const helpfulBtn = document.createElement('button');
    helpfulBtn.type = 'button';
    helpfulBtn.className = 'quick-btn';
    helpfulBtn.style.padding = '8px 12px';
    helpfulBtn.textContent = 'ตอบตรง';

    const notHelpfulBtn = document.createElement('button');
    notHelpfulBtn.type = 'button';
    notHelpfulBtn.className = 'quick-btn';
    notHelpfulBtn.style.padding = '8px 12px';
    notHelpfulBtn.textContent = 'ยังไม่ตรง';

    const status = document.createElement('span');
    status.style.fontSize = '12px';
    status.style.color = 'var(--gray)';
    status.style.alignSelf = 'center';

    async function submitFeedback(feedbackValue) {
      helpfulBtn.disabled = true;
      notHelpfulBtn.disabled = true;
      status.textContent = 'กำลังส่ง feedback...';
      try {
        const response = await fetch(apiUrl + '/analytics/chat-feedback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Session-Id': chatSessionId,
            'X-Visitor-Id': visitorId
          },
          body: JSON.stringify({
            session_id: chatSessionId,
            user_message: userText,
            bot_reply: botText,
            feedback_value: feedbackValue
          })
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(data.error || `HTTP ${response.status}`);
        }
        status.textContent = feedbackValue === 'helpful'
          ? 'รับทราบแล้วค้าบ คำตอบนี้ถือว่าตรง'
          : 'รับทราบแล้วค้าบ เดี๋ยวน้องเอาไปปรับต่อ';
      } catch (error) {
        status.textContent = 'ส่ง feedback ไม่สำเร็จ ลองใหม่ได้ค้าบ';
        helpfulBtn.disabled = false;
        notHelpfulBtn.disabled = false;
      }
    }

    helpfulBtn.addEventListener('click', () => submitFeedback('helpful'));
    notHelpfulBtn.addEventListener('click', () => submitFeedback('not_helpful'));

    actions.appendChild(helpfulBtn);
    actions.appendChild(notHelpfulBtn);
    actions.appendChild(status);
    return actions;
  }

  global.FreightChatMessageUtils = Object.freeze({
    isLikelyTrackingCode,
    escapeHtml,
    stripInternalSystemData,
    sanitizeUrl,
    renderSafeTextHtml,
    getTrackingSmallTalkReply,
    extractTrackingLinkData,
    openTrackingRedirect,
    renderTrackingCard,
    createFeedbackActions
  });
})(window);
