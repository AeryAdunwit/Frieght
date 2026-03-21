    // ── CONFIG ──
    const PROD_BACKEND_URL = 'https://frieght-fngh.onrender.com'; // <--- เปลี่ยนเป็น URL ของ Render เมื่อได้แล้ว
    
    const API_URL = (window.location.hostname === 'localhost' || 
                     window.location.hostname === '127.0.0.1' || 
                     window.location.protocol === 'file:') 
                    ? 'http://localhost:8000' 
                    : PROD_BACKEND_URL;

    // ── STATE ──
    const chatHistory = [];
    let activeChatTopic = null;
    let chatResponseMode = localStorage.getItem('chat_response_mode') === 'detail' ? 'detail' : 'quick';
    let lastChatTrigger = null;
    let visitorId = '';
    let chatSessionId = '';
    const MAX_HISTORY = 20;
    const ESCALATION_TRIGGERS = ['ไม่สามารถ', 'ขออภัย', 'ไม่ทราบ', 'ไม่มีข้อมูล', 'กรุณาติดต่อ', 'แนะนำให้ติดต่อ'];
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
      general: [
        { label: 'มีบริการอะไรบ้าง', text: 'มีบริการอะไรบ้าง' },
        { label: 'เวลาทำการ', text: 'เวลาทำการเป็นยังไง' }
      ],
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

    // ═══ DARK MODE ═══
    const darkMode = localStorage.getItem('dark') === 'true';
    if (darkMode) {
      document.documentElement.classList.add('dark');
      document.getElementById('theme-icon').className = 'fas fa-sun';
    }

    function toggleDark() {
      const isDark = document.documentElement.classList.toggle('dark');
      localStorage.setItem('dark', isDark);
      document.getElementById('theme-icon').className = isDark ? 'fas fa-sun' : 'fas fa-moon';
      showToast(isDark ? '🌙 โหมดมืด' : '☀️ โหมดสว่าง');
    }

    // ═══ TABS ═══
    function activateTab(tab) {
      document.querySelectorAll('.content').forEach(el => el.classList.remove('show'));
      document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
      document.getElementById(tab).classList.add('show');
      const matchingButton = Array.from(document.querySelectorAll('.tab-btn'))
        .find(btn => btn.getAttribute('onclick') === `switchTab('${tab}')`);
      if (matchingButton) matchingButton.classList.add('active');
    }

    function switchTab(tab) {
      activateTab(tab);
    }

    // ═══ TOAST ═══
    function showToast(msg) {
      const toast = document.createElement('div');
      toast.className = 'toast';
      toast.textContent = msg;
      document.body.appendChild(toast);
      setTimeout(() => toast.remove(), 2000);
    }

    // ═══ CHATBOT LOGIC ═══
    function toggleChat() {
      const chatBox = document.getElementById('chat-box');
      if (chatBox.classList.contains('open')) {
        closeChat();
      } else {
        openChat();
      }
    }

    function resetChat() {
      chatHistory.length = 0;
      activeChatTopic = null;
      document.getElementById('chat-messages').innerHTML = '';
      document.getElementById('escalation-bar').style.display = 'none';
      closeHandoffPanel();
      updateComposerState('general');
      showWelcomeMessage();
    }

    function setChatExpandedState(isOpen) {
      const chatBox = document.getElementById('chat-box');
      const toggleButton = document.getElementById('chat-toggle');
      chatBox.setAttribute('aria-hidden', String(!isOpen));
      toggleButton.setAttribute('aria-expanded', String(isOpen));
    }

    function openChat() {
      const chatBox = document.getElementById('chat-box');
      lastChatTrigger = document.activeElement instanceof HTMLElement ? document.activeElement : document.getElementById('chat-toggle');
      chatBox.classList.add('open');
      setChatExpandedState(true);
      if (chatHistory.length === 0) {
        showWelcomeMessage();
      }
      window.setTimeout(() => {
        document.getElementById('chat-input')?.focus();
      }, 0);
    }

    function closeChat() {
      const chatBox = document.getElementById('chat-box');
      chatBox.classList.remove('open');
      setChatExpandedState(false);
      closeHandoffPanel();
      if (lastChatTrigger && typeof lastChatTrigger.focus === 'function') {
        lastChatTrigger.focus();
      } else {
        document.getElementById('chat-toggle')?.focus();
      }
    }

    function updateComposerState(topic = 'general') {
      const safeTopic = TOPIC_COMPOSER_HINTS[topic] ? topic : 'general';
      const input = document.getElementById('chat-input');
      const hint = document.getElementById('chat-input-hint');
      if (input) {
        input.placeholder = TOPIC_COMPOSER_HINTS[safeTopic].placeholder;
      }
      if (hint) {
        const hintHtml = TOPIC_COMPOSER_HINTS[safeTopic].hint || '';
        hint.innerHTML = hintHtml;
        hint.style.display = hintHtml ? 'block' : 'none';
      }
      renderChatSuggestions(safeTopic);
      renderIntakeCoach(safeTopic);
    }

    function updateResponseModeUi() {
      const quickBtn = document.getElementById('chat-mode-quick');
      const detailBtn = document.getElementById('chat-mode-detail');
      const caption = document.getElementById('chat-mode-caption');
      if (quickBtn) {
        quickBtn.classList.toggle('active', chatResponseMode === 'quick');
        quickBtn.setAttribute('aria-pressed', chatResponseMode === 'quick' ? 'true' : 'false');
      }
      if (detailBtn) {
        detailBtn.classList.toggle('active', chatResponseMode === 'detail');
        detailBtn.setAttribute('aria-pressed', chatResponseMode === 'detail' ? 'true' : 'false');
      }
      if (caption) {
        caption.textContent = RESPONSE_MODE_LABELS[chatResponseMode] || RESPONSE_MODE_LABELS.quick;
      }
    }

    function setChatResponseMode(mode) {
      chatResponseMode = mode === 'detail' ? 'detail' : 'quick';
      localStorage.setItem('chat_response_mode', chatResponseMode);
      updateResponseModeUi();
      showToast(chatResponseMode === 'detail'
        ? 'โอเคค้าบ รอบนี้น้องจะตอบละเอียดขึ้นอีกนิด'
        : 'โอเคค้าบ รอบนี้น้องจะตอบสั้น กระชับก่อน');
    }

    function normalizeSuggestionTopic(topic) {
      const safeTopic = String(topic || '').trim().toLowerCase();
      if (TOPIC_SUGGESTIONS[safeTopic]) return safeTopic;
      if (safeTopic === 'general_chat' || safeTopic === 'longform_consult') return 'general';
      if (safeTopic === 'document') return 'documents';
      return 'general';
    }

    function inferSuggestionTopicFromContext(userText = '', botText = '') {
      const combined = `${activeChatTopic || ''} ${userText} ${botText}`.toLowerCase();
      if (/handoff|ให้ทีมช่วย|ติดต่อกลับ|โทรกลับ/.test(combined)) return 'handoff';
      if (/solar|ธุรกิจ em|hub em|แผง/.test(combined)) return 'solar';
      if (/tracking|ติดตาม|เลข do|\b\d{6,}\b/.test(combined)) return 'tracking';
      if (/ราคา|ค่าส่ง|ประเมิน/.test(combined)) return 'pricing';
      if (/จอง|เข้ารับ|เหมาคัน|รถใหญ่/.test(combined)) return 'booking';
      if (/เคลม|ชำรุด|เสียหาย|ส่งผิด|ของหาย/.test(combined)) return 'claim';
      if (/เอกสาร/.test(combined)) return 'documents';
      if (/กี่วัน|ตัดรอบ|ช้า|ระยะเวลา/.test(combined)) return 'timeline';
      if (/ทั่วประเทศ|ต่างจังหวัด|พื้นที่/.test(combined)) return 'coverage';
      return normalizeSuggestionTopic(activeChatTopic || inferCurrentIntentName());
    }

    function buildSmartSuggestions(topic, lastUser = '', lastBot = '') {
      const safeTopic = normalizeSuggestionTopic(topic);
      const suggestions = [...(TOPIC_SUGGESTIONS[safeTopic] || TOPIC_SUGGESTIONS.general)];
      const recentText = `${collectRecentChatText()} ${lastUser} ${lastBot}`.toLowerCase();
      const memory = inferConversationMemory(safeTopic, recentText);

      if (safeTopic === 'pricing') {
        if (!memory.route) suggestions.unshift({ label: 'ต้นทาง/ปลายทาง', text: 'ต้นทาง กรุงเทพ ปลายทาง ขอนแก่น' });
        else if (!memory.product) suggestions.unshift({ label: 'สินค้า Solar', text: 'สินค้าเป็นแผง Solar' });
        else if (!memory.quantity) suggestions.unshift({ label: 'จำนวน 48 แผง', text: 'จำนวน 48 แผง' });
      }
      if (safeTopic === 'solar') {
        if (!memory.route) suggestions.unshift({ label: 'อยุธยา → ขอนแก่น', text: 'ต้นทาง อยุธยา ปลายทาง ขอนแก่น' });
        else if (!memory.quantity) suggestions.unshift({ label: 'จำนวน 48 แผง', text: 'จำนวน 48 แผง รุ่นสินค้า Jinko' });
        else if (!memory.schedule) suggestions.unshift({ label: 'ส่งสัปดาห์หน้า', text: 'อยากส่งสัปดาห์หน้า' });
      }
      if (safeTopic === 'booking') {
        if (!memory.route) suggestions.unshift({ label: 'บางนา → ลำลูกกา', text: 'รับจาก บางนา ไป ลำลูกกา' });
        else if (!memory.quantity) suggestions.unshift({ label: 'ของ 10 ลัง', text: 'ของ 10 ลัง' });
        else if (!memory.schedule) suggestions.unshift({ label: 'เข้ารับพรุ่งนี้บ่าย', text: 'อยากให้เข้ารับพรุ่งนี้บ่าย' });
      }
      if (safeTopic === 'claim') {
        if (!memory.job) suggestions.unshift({ label: 'ใส่เลข DO', text: 'DO 1314639771' });
        else if (!memory.issue) suggestions.unshift({ label: 'สินค้าชำรุด', text: 'สินค้าชำรุด มุมบุบ' });
        else if (!memory.evidence) suggestions.unshift({ label: 'มีรูปหลักฐานครบ', text: 'มีรูปหลักฐานครบแล้ว' });
      }
      if (safeTopic === 'tracking' && !memory.job) {
        suggestions.unshift({ label: 'ใส่เลข DO', text: '1314639771' });
      }

      return suggestions.slice(0, 4);
    }

    function handleSuggestionAction(item) {
      if (!item) return;
      if (item.action === 'handoff') {
        handleHandoffTopic();
        return;
      }
      if (item.action === 'handoff_form') {
        handleHandoffTopic();
        openHandoffPanel();
        return;
      }
      if (item.text) {
        sendMessage(item.text);
      }
    }

    function renderChatSuggestions(topic = 'general', lastUser = '', lastBot = '') {
      const target = document.getElementById('chat-suggestions');
      if (!target) return;
      const suggestions = buildSmartSuggestions(topic, lastUser, lastBot);
      if (!suggestions.length) {
        target.innerHTML = '';
        return;
      }
      target.innerHTML = suggestions.map((item, index) => `
        <button class="chat-suggestion-btn" type="button" data-suggestion-index="${index}">${escapeHtml(item.label || item.text || 'ถามต่อ')}</button>
      `).join('');
      target.querySelectorAll('[data-suggestion-index]').forEach((button) => {
        button.addEventListener('click', () => {
          const idx = Number(button.getAttribute('data-suggestion-index'));
          handleSuggestionAction(suggestions[idx]);
        });
      });
    }

    showWelcomeMessage = function() {
      const messagesContainer = document.getElementById('chat-messages');
      document.getElementById('chat-back-btn').style.display = 'none';
      messagesContainer.innerHTML = `
        <div id="welcome-card" style="padding: 12px;">
          <div style="background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin-bottom: 12px;">
            <p style="margin: 0 0 6px; font-weight: 700; color: var(--primary);">สวัสดีค้าบ ถามสั้น ตอบไว พร้อมลุย</p>
            <p style="margin: 0; font-size: 13px; color: var(--gray);">เลือกหัวข้อได้เลย หรือพิมพ์ตรง ๆ มา น้องโกดังจับประเด็นให้เองค้าบ</p>
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <button class="quick-btn" onclick="handleCalculateAction()">📦 คำนวณค่าส่ง</button>
            <button class="quick-btn" onclick="handleBookingAction()">🚚 จองส่งสินค้า เหมาคัน/ขนาดใหญ่</button>
            <button class="quick-btn" onclick="quickAsk('วิธีติดตามสถานะพัสดุ')">🔍 ติดตามพัสดุ</button>
            <button class="quick-btn" onclick="quickAsk('ธุรกิจ EM คืออะไร')">🏭 ส่ง Solar ผ่าน Hub</button>
            <button class="quick-btn" onclick="handleHandoffTopic()">🤝 ให้ทีมช่วยต่อ</button>
            <button class="quick-btn" onclick="handleOtherInquiry()" style="grid-column: span 2;">💬 อื่นๆ (สอบถามเพิ่มเติม)</button>
          </div>
        </div>
      `;
      renderChatSuggestions('general');
    };

    handleCalculateAction = function() {
      const card = document.getElementById('welcome-card');
      if (card) card.remove();
      document.getElementById('chat-back-btn').style.display = 'block';
      activeChatTopic = 'pricing';
      updateComposerState('pricing');
      activateTab('shipping');
      appendMessage("bot", "จะเช็กราคาไว ๆ ส่งต้นทาง ปลายทาง กับประเภทสินค้ามาได้เลยค้าบ");
    };

    handleBookingAction = function() {
      const card = document.getElementById('welcome-card');
      if (card) card.remove();
      document.getElementById('chat-back-btn').style.display = 'block';
      activeChatTopic = 'booking';
      updateComposerState('booking');
      activateTab('booking');

      const link = "https://aeryadunwit.github.io/BookingSolar/";
      appendMessage("bot", `งานเหมาคันหรือของชิ้นใหญ่ กดหน้าจองต่อได้เลยค้าบ<br><br><a href="${link}" target="_blank" style="display: inline-block; background: var(--primary); color: white; padding: 10px 20px; border-radius: 999px; text-decoration: none; font-weight: bold; margin-top: 5px;"><i class="fas fa-external-link-alt"></i> เปิดหน้าจองงาน</a>`, true);

      const container = document.getElementById('chat-messages');
      const followupDiv = document.createElement('div');
      followupDiv.className = 'message bot';
      followupDiv.innerHTML = `
        <p style="margin-bottom: 10px;">อยากได้สรุปขั้นตอนต่อไหมค้าบ</p>
        <div style="display: flex; gap: 10px;">
          <button class="quick-btn" style="flex:1; text-align:center; justify-content:center;" onclick="handleBookingFollowup(true)">สรุปขั้นตอน</button>
          <button class="quick-btn" style="flex:1; text-align:center; justify-content:center;" onclick="handleBookingFollowup(false)">ไว้ก่อนน้า</button>
        </div>
      `;
      container.appendChild(followupDiv);
      container.scrollTop = container.scrollHeight;
    };

    handleOtherInquiry = function() {
      const card = document.getElementById('welcome-card');
      if (card) card.remove();
      document.getElementById('chat-back-btn').style.display = 'block';
      activeChatTopic = 'general';
      updateComposerState('general');
      appendMessage("bot", "ถามมาได้เลยค้าบ เรื่องงานก็ตอบ เรื่องเหงาก็คุยได้");
      appendMessage("bot", "ถ้าพิมพ์ยาวมา เดี๋ยวน้องช่วยจับประเด็นให้เองค้าบ");
    };

    handleHandoffTopic = function() {
      const card = document.getElementById('welcome-card');
      if (card) card.remove();
      document.getElementById('chat-back-btn').style.display = 'block';
      activeChatTopic = 'handoff';
      updateComposerState('handoff');
      openHandoffPanel('ต้องการให้ทีมช่วยคุยต่อ');
    };

    quickAsk = function(prompt) {
      const card = document.getElementById('welcome-card');
      if (card) card.remove();
      document.getElementById('chat-back-btn').style.display = 'block';
      if (prompt.includes('ติดตาม')) {
        activeChatTopic = 'tracking';
        updateComposerState('tracking');
        activateTab('tracking');
      } else if (prompt.includes('Solar') || prompt.includes('ธุรกิจ EM') || prompt.includes('HUB EM')) {
        activeChatTopic = 'solar';
        updateComposerState('solar');
      } else if (prompt.includes('ค่าส่ง') || prompt.includes('ราคา')) {
        activeChatTopic = 'pricing';
        updateComposerState('pricing');
        activateTab('shipping');
      } else {
        activeChatTopic = null;
        updateComposerState('general');
      }
      sendMessage(prompt);
    };

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
      const source = text || '';
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
        {
          test: /(hi|hello|หวัดดี|สวัสดี|ดีจ้า|ดีครับ|ดีคับ)/i,
          reply: 'สวัสดีค้าบ จะคุยเล่นก่อน หรือส่ง DO มาให้เช็กเลยก็ได้'
        },
        {
          test: /(ขอบคุณ|thank|thx|thanks)/i,
          reply: 'ยินดีค้าบ มี DO ต่อก็ส่งมาได้เลย หรือจะคุยเล่นรอผลก็ได้'
        },
        {
          test: /(หิว|เหนื่อย|ง่วง|เหงา|เบื่อ|เครียด|ท้อ|เศร้า)/i,
          reply: 'โอ๋เอ๋ก่อนค้าบ เหนื่อยก็พักได้ เดี๋ยวค่อยส่ง DO มา น้องช่วยต่อให้'
        },
        {
          test: /(ชื่ออะไร|ชื่อไร|ใคร|เป็นใคร)/i,
          reply: 'น้องโกดังค้าบ เช็กพัสดุก็ได้ คุยเล่นก็ไหว'
        },
        {
          test: /(ทำอะไรได้|ช่วยอะไรได้|ทำไรได้)/i,
          reply: 'น้องช่วยเช็กพัสดุ ตอบเรื่องบริการ และคุยเล่นได้ค้าบ'
        },
        {
          test: /(555|ฮ่า|ตลก|มุก|ขำ)/i,
          reply: 'มุกวันนี้คือ ของอาจยังไม่ถึง แต่เดดไลน์ถึงก่อนค้าบ หายขำแล้วส่ง DO มาได้เลย'
        },
        {
          test: /(ฝันดี|good night|gn|นอนก่อน)/i,
          reply: 'ฝันดีค้าบ ตื่นมาแล้วค่อยทักน้องใหม่ได้เสมอ'
        },
        {
          test: /(รักนะ|คิดถึง|miss you|love you)/i,
          reply: 'เขินค้าบ แต่ยังทำงานไหวนะ ส่ง DO มาได้เลยถ้าจะให้ช่วยต่อ'
        },
        {
          test: /(กินข้าว|กินอะไร|ข้าวยัง)/i,
          reply: 'น้องกินข้อมูลแทนข้าวค้าบ แต่คุณอย่าลืมกินข้าวนะ แล้วค่อยส่ง DO มาให้น้อง'
        },
        {
          test: /(อยู่ไหม|ว่างไหม|คุยได้ไหม|อยู่รึเปล่า)/i,
          reply: 'อยู่ค้าบ จะคุยเล่นหรือส่ง DO มาให้น้องเช็คก็ได้'
        }
      ];

      for (const item of patterns) {
        if (item.test.test(normalized)) return item.reply;
      }

      if (normalized.length <= 80) {
        return 'คุยได้ค้าบ น้องพร้อมฟัง แต่ถ้าจะเช็กพัสดุไว ๆ ส่ง DO มาได้เลย';
      }
      return null;
    }

    function extractTrackingLinkData(text) {
      if (!text) return null;
      const urlMatch = text.match(/https?:\/\/[^\s]+/);
      if (!urlMatch) return null;

      const trackingUrl = sanitizeUrl(urlMatch[0]);
      if (!trackingUrl) return null;
      const isSkyfrog = trackingUrl.includes('aeryadunwit.github.io/tracktrace');
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

    function renderTrackingCard(text) {
      const trackingData = extractTrackingLinkData(text);
      if (!trackingData) return null;

      const { trackingUrl, summary, isSkyfrog, isPorlor } = trackingData;
      if (isSkyfrog && !isPorlor) {
        return `
          <div style="display:flex; flex-direction:column; gap:10px;">
            <div>${summary}</div>
            <div style="border:1px solid var(--border); border-radius:14px; overflow:hidden; background:linear-gradient(135deg, rgba(233, 30, 52, 0.08), rgba(255,255,255,0.98));">
              <div style="padding:12px 14px; font-weight:700; color:var(--primary);">
                เปิด Skyfrog ในแท็บใหม่ได้เลยค้าบ
              </div>
              <div style="padding:0 14px 14px; color:var(--gray); font-size:13px; line-height:1.5;">
                น้องโกดังผูกลิงก์ค้นหาสถานะไว้ให้แล้ว กดเปิดในแท็บใหม่ได้เลยค้าบ
              </div>
              <div style="padding:0 14px 14px; display:flex; gap:10px; flex-wrap:wrap;">
                <a href="${trackingUrl}" target="_blank" rel="noopener noreferrer" style="display:inline-block; border:1px solid var(--primary); color:var(--primary); padding:10px 14px; border-radius:10px; text-decoration:none; font-weight:700;">
                  เปิด Skyfrog ในแท็บใหม่
                </a>
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
              <div style="padding:12px 14px; font-weight:700; color:var(--primary);">
                เปิดหน้าเช็ค Porlor ในแท็บใหม่พร้อมเลขค้นหาได้เลยค้าบ
              </div>
              <div style="padding:0 14px 14px; color:var(--gray); font-size:13px; line-height:1.5;">
                น้องโกดังเตรียมหน้าเช็คของ Porlor พร้อมเลข DO ให้แล้ว กดเปิดต่อได้เลยค้าบ
              </div>
              <div style="padding:0 14px 14px; display:flex; gap:10px; flex-wrap:wrap;">
                <a href="${trackingUrl}" target="_blank" rel="noopener noreferrer" style="display:inline-block; border:1px solid var(--primary); color:var(--primary); padding:10px 14px; border-radius:10px; text-decoration:none; font-weight:700;">
                  เปิด Porlor ในแท็บใหม่
                </a>
              </div>
            </div>
          </div>
        `;
      }

      return `
        <div style="display:flex; flex-direction:column; gap:10px;">
          <div>${summary}</div>
          <div style="border:1px solid var(--border); border-radius:14px; overflow:hidden; background:linear-gradient(135deg, rgba(233, 30, 52, 0.08), rgba(255,255,255,0.98));">
            <div style="padding:12px 14px; font-weight:700; color:var(--primary);">
              เปิดหน้าเช็คสถานะในแท็บใหม่ได้เลยค้าบ
            </div>
            <div style="padding:0 14px 14px; color:var(--gray); font-size:13px; line-height:1.5;">
              น้องโกดังแปะลิงก์เว็บขนส่งไว้ให้แล้ว กดเปิดในแท็บใหม่ได้เลยค้าบ
            </div>
            <div style="padding:0 14px 14px; display:flex; gap:10px; flex-wrap:wrap;">
              <a href="${trackingUrl}" target="_blank" rel="noopener noreferrer" style="display:inline-block; border:1px solid var(--primary); color:var(--primary); padding:10px 14px; border-radius:10px; text-decoration:none; font-weight:700;">
                เปิดลิงก์ในแท็บใหม่
              </a>
            </div>
          </div>
        </div>
      `;
    }

    function createFeedbackActions(userText, botText) {
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
          const response = await fetch(API_URL + '/analytics/chat-feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
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

    function getLastChatTurn(role) {
      for (let index = chatHistory.length - 1; index >= 0; index -= 1) {
        if (chatHistory[index]?.role === role) {
          return chatHistory[index]?.content || '';
        }
      }
      return '';
    }

    function collectRecentChatText() {
      return [
        getLastChatTurn('user'),
        getLastChatTurn('model'),
        ...chatHistory.slice(-6).map(item => item?.content || '')
      ].filter(Boolean).join('\n');
    }

    function inferConversationMemory(topic, text = '') {
      const source = String(text || '').toLowerCase();
      const route = /ต้นทาง|ปลายทาง|จาก|ไป|รับจาก|ส่งไป|ถึง/.test(source);
      const quantity = /\d/.test(source) && /(แผง|ชิ้น|พาเลท|พาเลต|ลัง|กล่อง|กก|kg|ตัน|คัน)/.test(source);
      const product = /(solar|โซลาร์|แผง|inverter|อินเวอร์เตอร์|สินค้า|อะไหล่|เครื่อง)/.test(source);
      const schedule = /(วันนี้|พรุ่งนี้|สัปดาห์|อาทิตย์|วันที่|เช้า|บ่าย|เย็น|ด่วน)/.test(source);
      const jobMatch = source.match(/\b\d{6,}\b/);
      const issue = /(เสียหาย|ชำรุด|หาย|ส่งผิด|แตก|บุบ|ปัญหา)/.test(source);
      const evidence = /(รูป|ภาพ|หลักฐาน|วิดีโอ|video)/.test(source);
      return {
        topic,
        route,
        quantity,
        product,
        schedule,
        job: jobMatch ? jobMatch[0] : '',
        issue,
        evidence
      };
    }

    function inferContactSeed(text) {
      const source = String(text || '');
      const phoneMatch = source.match(/(?:0\d{8,9})/);
      if (phoneMatch) {
        return { value: phoneMatch[0], channel: 'phone' };
      }
      const emailMatch = source.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i);
      if (emailMatch) {
        return { value: emailMatch[0], channel: 'email' };
      }
      const lineMatch = source.match(/(?:line\s*[:=]?\s*@?[a-z0-9._-]+)/i);
      if (lineMatch) {
        return { value: lineMatch[0].replace(/^line\s*[:=]?\s*/i, '').trim(), channel: 'line' };
      }
      return { value: '', channel: '' };
    }

    function buildHandoffSeed(topic, userText) {
      const lastUser = userText || getLastChatTurn('user') || '';
      const jobMatch = collectRecentChatText().match(/\b\d{6,}\b/);
      const jobNumber = jobMatch ? jobMatch[0] : '';
      const summary = buildHandoffSummary(topic);
      const missingHint = summary.missing.length ? ` | ยังขาด ${summary.missing.join(', ')}` : '';

      if (topic === 'tracking') {
        return jobNumber
          ? `ต้องการให้ทีมช่วยตามงาน DO ${jobNumber}${missingHint}`
          : 'ต้องการให้ทีมช่วยตามสถานะพัสดุต่อ';
      }
      if (topic === 'pricing') {
        return `ต้องการให้ทีมช่วยประเมินราคาต่อ${lastUser ? ` | ${lastUser}` : ''}${missingHint}`.trim();
      }
      if (topic === 'booking') {
        return `ต้องการให้ทีมช่วยคุยต่อเรื่องจองงาน${lastUser ? ` | ${lastUser}` : ''}${missingHint}`.trim();
      }
      if (topic === 'solar') {
        return `ต้องการให้ทีมช่วยคุยต่อเรื่อง Solar${lastUser ? ` | ${lastUser}` : ''}${missingHint}`.trim();
      }
      if (topic === 'claim') {
        return `ต้องการให้ทีมช่วยดูเคสเคลมต่อ${jobNumber ? ` | DO ${jobNumber}` : ''}${missingHint}`.trim();
      }
      return userText || lastUser || 'ต้องการให้ทีมช่วยคุยต่อ';
    }

    function buildHandoffSummary(topic) {
      const memory = inferConversationMemory(topic, collectRecentChatText());
      const chips = [];

      if (memory.job) chips.push(`DO ${memory.job}`);
      if (memory.route) chips.push('มีต้นทาง/ปลายทางแล้ว');
      if (memory.quantity) chips.push('มีจำนวนงานแล้ว');
      if (memory.product) chips.push('มีประเภทสินค้าแล้ว');
      if (memory.schedule) chips.push('มีช่วงเวลางานแล้ว');
      if (memory.issue) chips.push('มีอาการปัญหาแล้ว');
      if (memory.evidence) chips.push('มีหลักฐานแล้ว');

      const missingMap = {
        solar: [
          !memory.route && 'ต้นทาง/ปลายทาง',
          !memory.quantity && 'จำนวนแผง',
          !memory.product && 'รุ่นหรือประเภทสินค้า',
          !memory.schedule && 'วันส่ง'
        ],
        pricing: [
          !memory.route && 'ต้นทาง/ปลายทาง',
          !memory.product && 'ประเภทสินค้า',
          !memory.quantity && 'จำนวนหรือน้ำหนัก'
        ],
        booking: [
          !memory.route && 'ต้นทาง/ปลายทาง',
          !memory.product && 'ประเภทสินค้า',
          !memory.quantity && 'จำนวนงาน',
          !memory.schedule && 'ช่วงเวลาเข้ารับ'
        ],
        claim: [
          !memory.job && 'เลข DO',
          !memory.issue && 'อาการปัญหา',
          !memory.evidence && 'รูปหรือหลักฐาน'
        ],
        tracking: [
          !memory.job && 'เลข DO'
        ]
      };

      const missing = (missingMap[topic] || []).filter(Boolean).slice(0, 3);
      return { chips, missing };
    }

    function renderHandoffSummary(topic = activeChatTopic || inferCurrentIntentName()) {
      const target = document.getElementById('handoff-summary');
      if (!target) return;
      const { chips, missing } = buildHandoffSummary(topic);
      if (!chips.length && !missing.length) {
        target.style.display = 'none';
        target.innerHTML = '';
        return;
      }
      target.style.display = 'flex';
      const chipHtml = chips.length
        ? `<div class="handoff-summary-list">${chips.map((chip) => `<span class="handoff-summary-chip">${escapeHtml(chip)}</span>`).join('')}</div>`
        : '';
      const note = missing.length
        ? `ยังขาดอีกนิดค้าบ: ${missing.join(', ')}`
        : 'ข้อมูลหลักเริ่มครบแล้วค้าบ ทีมหยิบไปคุยต่อได้ไวขึ้น';
      target.innerHTML = `
        <div class="handoff-summary-title">ข้อมูลที่น้องจับได้จากแชตนี้</div>
        ${chipHtml}
        <div class="handoff-summary-note">${escapeHtml(note)}</div>
      `;
    }

    function renderIntakeCoach(topic = activeChatTopic || inferCurrentIntentName()) {
      const target = document.getElementById('chat-intake-coach');
      if (!target) return;
      const normalizedTopic = normalizeSuggestionTopic(topic);
      const supportedTopics = ['solar', 'pricing', 'booking', 'claim', 'tracking'];
      if (!supportedTopics.includes(normalizedTopic)) {
        target.style.display = 'none';
        target.innerHTML = '';
        return;
      }

      const { chips, missing } = buildHandoffSummary(normalizedTopic);
      const ready = missing.length === 0;
      const titleMap = {
        solar: 'เช็กข้อมูลงาน Solar',
        pricing: 'เช็กข้อมูลประเมินราคา',
        booking: 'เช็กข้อมูลจองงาน',
        claim: 'เช็กข้อมูลเคลม',
        tracking: 'เช็กข้อมูลติดตามงาน'
      };
      const line = ready
        ? 'ข้อมูลเริ่มครบแล้วค้าบ ถ้าจะให้ทีมช่วยต่อ กดหัวข้อให้ทีมช่วยต่อได้เลย'
        : `ตอนนี้ยังขาด: ${missing.join(', ')}`;
      const chipHtml = chips.length
        ? `<div class="chat-intake-list">${chips.map((chip) => `<span class="chat-intake-chip">${escapeHtml(chip)}</span>`).join('')}</div>`
        : '';
      target.style.display = 'flex';
      target.innerHTML = `
        <div class="chat-intake-head">
          <div class="chat-intake-title">${escapeHtml(titleMap[normalizedTopic] || 'เช็กข้อมูลงาน')}</div>
          <span class="chat-intake-badge ${ready ? 'ready' : ''}">${ready ? 'พร้อมส่งต่อ' : 'ยังไม่ครบ'}</span>
        </div>
        <div class="chat-intake-line">${escapeHtml(line)}</div>
        ${chipHtml}
      `;
    }

    function inferCurrentIntentName() {
      if (activeChatTopic === 'tracking') return 'tracking';
      const lastUser = getLastChatTurn('user').toLowerCase();
      if (/solar|ธุรกิจ em|hub/.test(lastUser)) return 'solar';
      if (/ราคา|quotation|quote|ค่าส่ง/.test(lastUser)) return 'pricing';
      if (/จอง|booking|เข้ารับ|เหมาคัน|รถใหญ่/.test(lastUser)) return 'booking';
      if (/เคลม|claim|เสียหาย|ส่งผิด/.test(lastUser)) return 'claim';
      if (/เอกสาร/.test(lastUser)) return 'document';
      if (/กี่วัน|ตัดรอบ|ช้า/.test(lastUser)) return 'timeline';
      if (/ทั่วประเทศ|ต่างจังหวัด|พื้นที่/.test(lastUser)) return 'coverage';
      return activeChatTopic || 'general_chat';
    }

    function openHandoffPanel(seedText = '') {
      const panel = document.getElementById('handoff-panel');
      const nameEl = document.getElementById('handoff-name');
      const contactEl = document.getElementById('handoff-contact');
      const channelEl = document.getElementById('handoff-channel');
      const note = document.getElementById('handoff-note');
      const status = document.getElementById('handoff-status');
      if (!panel || !nameEl || !contactEl || !channelEl || !note || !status) return;
      const lastUser = getLastChatTurn('user');
      const recentText = collectRecentChatText();
      const contactSeed = inferContactSeed(recentText);
      if (!contactEl.value.trim() && contactSeed.value) {
        contactEl.value = contactSeed.value;
      }
      if ((!channelEl.value || channelEl.value === 'phone') && contactSeed.channel) {
        channelEl.value = contactSeed.channel;
      }
      if (!nameEl.value.trim() && activeChatTopic === 'handoff') {
        nameEl.placeholder = 'เช่น โกดัง / ทีมคลัง';
      }
      if (!note.value.trim()) {
        note.value = buildHandoffSeed(activeChatTopic, seedText || lastUser);
      }
      status.textContent = contactEl.value.trim()
        ? 'ข้อมูลเริ่มครบแล้วค้าบ กดส่งต่อให้ทีมได้เลย'
        : 'ถ้าใส่ช่องทางติดต่อไว้ด้วย ทีมจะหยิบไปต่อได้ไวขึ้นค้าบ';
      renderHandoffSummary(activeChatTopic || inferCurrentIntentName());
      panel.classList.add('open');
      (contactEl.value.trim() ? note : contactEl).focus();
    }

    function closeHandoffPanel() {
      const panel = document.getElementById('handoff-panel');
      if (panel) {
        panel.classList.remove('open');
      }
    }

    async function submitHandoffRequest() {
      const nameEl = document.getElementById('handoff-name');
      const contactEl = document.getElementById('handoff-contact');
      const channelEl = document.getElementById('handoff-channel');
      const noteEl = document.getElementById('handoff-note');
      const statusEl = document.getElementById('handoff-status');
      const submitBtn = document.getElementById('handoff-submit-btn');
      if (!nameEl || !contactEl || !channelEl || !noteEl || !statusEl || !submitBtn) return;

      const customerName = nameEl.value.trim();
      const contactValue = contactEl.value.trim();
      const requestNote = noteEl.value.trim();
      const userMessage = getLastChatTurn('user');
      const botReply = getLastChatTurn('model');
      const jobMatch = `${userMessage} ${requestNote}`.match(/\b\d{6,}\b/);
      const jobNumber = jobMatch ? jobMatch[0] : '';

      if (!contactValue && !requestNote) {
        statusEl.textContent = 'ใส่ช่องทางติดต่อหรือสรุปสั้น ๆ ให้ทีมสักนิดก่อนค้าบ';
        return;
      }

      submitBtn.disabled = true;
      statusEl.textContent = 'กำลังส่งต่อให้ทีมค้าบ...';

      try {
        const response = await fetch(API_URL + '/analytics/handoff-request', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: chatSessionId,
            customer_name: customerName,
            contact_value: contactValue,
            preferred_channel: channelEl.value || 'phone',
            request_note: requestNote,
            user_message: userMessage,
            bot_reply: botReply,
            intent_name: inferCurrentIntentName(),
            source: 'widget_handoff',
            job_number: jobNumber
          })
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(data.error || `HTTP ${response.status}`);
        }
        statusEl.textContent = 'ส่งให้ทีมแล้วค้าบ เดี๋ยวทีมตามต่อจากข้อมูลชุดนี้ให้';
        appendMessage('bot', 'รับเรื่องให้แล้วค้าบ ทีมจะเห็นบริบทจากแชตนี้ต่อให้เลย ถ้ามีอะไรเพิ่ม พิมพ์ทิ้งไว้ได้อีก');
        noteEl.value = '';
        submitBtn.textContent = 'ส่งแล้วค้าบ';
        setTimeout(() => {
          submitBtn.disabled = false;
          submitBtn.textContent = 'ส่งให้ทีมต่อ';
        }, 1500);
      } catch (error) {
        statusEl.textContent = 'ส่งต่อให้ทีมยังไม่สำเร็จ ลองใหม่ได้ค้าบ';
        submitBtn.disabled = false;
      }
    }

    function appendMessage(role, text, isHTML = false) {
      const container = document.getElementById('chat-messages');
      const msgDiv = document.createElement('div');
      msgDiv.className = `message ${role}`;
      
      if (isHTML) {
        msgDiv.innerHTML = text;
      } else {
        msgDiv.innerHTML = renderSafeTextHtml(text);
      }
      
      container.appendChild(msgDiv);
      container.scrollTop = container.scrollHeight;
    }

    function showTypingIndicator() {
      const container = document.getElementById('chat-messages');
      const typing = document.createElement('div');
      typing.id = 'typing-indicator';
      typing.className = 'message bot';
      typing.style.fontStyle = 'italic';
      typing.textContent = 'น้องโกดัง กำลังพิมพ์...';
      container.appendChild(typing);
      container.scrollTop = container.scrollHeight;
    }

    function hideTypingIndicator() {
      const typing = document.getElementById('typing-indicator');
      if (typing) typing.remove();
    }

    async function sendMessageFromInput() {
      const input = document.getElementById('chat-input');
      const text = input.value.trim();
      if (!text) return;
      input.value = '';
      const card = document.getElementById('welcome-card');
      if (card) {
        card.remove();
        document.getElementById('chat-back-btn').style.display = 'block'; // Show back button on first message
      }
      await sendMessage(text);
    }

    async function sendMessage(userText) {
      const TIMEOUT_MS = 30000;
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

      const trackingSmallTalkReply =
        activeChatTopic === 'tracking' ? getTrackingSmallTalkReply(userText) : null;
      if (trackingSmallTalkReply) {
        appendMessage("user", userText);
        appendMessage("bot", trackingSmallTalkReply);
        renderChatSuggestions('tracking', userText, trackingSmallTalkReply);
        renderIntakeCoach('tracking');
        renderHandoffSummary();
        clearTimeout(timer);
        return;
      }

      chatHistory.push({ role: "user", content: userText });
      appendMessage("user", userText);
      showTypingIndicator();

      try {
        const res = await fetch(API_URL + '/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          signal: controller.signal,
          body: JSON.stringify({
            message: userText,
            history: chatHistory.slice(0, -1),
            session_id: chatSessionId,
            response_mode: chatResponseMode
          })
        });

        hideTypingIndicator();

        if (!res.ok) {
          if (res.status === 429) {
            appendMessage("bot", "ส่งข้อความถี่เกินไป กรุณารอสักครู่");
          } else {
            const data = await res.json().catch(() => ({}));
            appendMessage("bot", "เกิดข้อผิดพลาด: " + (data.error || `HTTP ${res.status}`));
          }
          chatHistory.pop();
          return;
        }

        const container = document.getElementById('chat-messages');
        const botMsgDiv = document.createElement('div');
        botMsgDiv.className = 'message bot';
        container.appendChild(botMsgDiv);
        let fullResponse = '';

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const data = line.slice(6);

            if (data === '[DONE]') break;
            if (data.startsWith('[ERROR]')) {
              const errorText = data.replace('[ERROR]', '').trim() || 'เกิดข้อผิดพลาดในการประมวลผล';
              botMsgDiv.innerHTML = `<strong>เกิดข้อผิดพลาด:</strong><br>${renderSafeTextHtml(errorText)}`;
              fullResponse = `เกิดข้อผิดพลาด: ${errorText}`;
              container.scrollTop = container.scrollHeight;
              break;
            }

            fullResponse += data;
            botMsgDiv.innerHTML = renderSafeTextHtml(fullResponse);
            container.scrollTop = container.scrollHeight;
          }
        }

        if (!fullResponse) {
          fullResponse = 'ไม่พบข้อความตอบกลับจากระบบ';
          botMsgDiv.textContent = fullResponse;
        }

        const trackingCardHtml = renderTrackingCard(fullResponse);
        if (trackingCardHtml) {
          botMsgDiv.innerHTML = trackingCardHtml;
          const trackingData = extractTrackingLinkData(fullResponse);
          if (trackingData) {
            setTimeout(() => openTrackingRedirect(trackingData.trackingUrl), 250);
          }
        }

        botMsgDiv.appendChild(createFeedbackActions(userText, fullResponse));

        chatHistory.push({ role: "model", content: fullResponse });
        checkEscalation(fullResponse);
        const nextTopic = inferSuggestionTopicFromContext(userText, fullResponse);
        renderChatSuggestions(nextTopic, userText, fullResponse);
        renderIntakeCoach(nextTopic);
        renderHandoffSummary();

        if (chatHistory.length > MAX_HISTORY) {
          chatHistory.splice(0, 2);
        }
      } catch (err) {
        hideTypingIndicator();
        if (err.name === 'AbortError') {
          appendMessage("bot", "ระบบใช้เวลาตอบนานเกินไป กรุณาลองอีกครั้ง");
        } else {
          appendMessage("bot", "ไม่สามารถเชื่อมต่อได้ในขณะนี้\nรายละเอียด: " + (err.message || 'unknown error'));
        }
        chatHistory.pop();
        const fallbackTopic = inferSuggestionTopicFromContext(userText);
        renderChatSuggestions(fallbackTopic, userText, '');
        renderIntakeCoach(fallbackTopic);
        renderHandoffSummary();
      } finally {
        clearTimeout(timer);
      }
    }

    function checkEscalation(aiResponse) {
      const shouldEscalate = ESCALATION_TRIGGERS.some(kw => aiResponse.includes(kw));
      document.getElementById('escalation-bar').style.display = 'none';
      return shouldEscalate;
    }

    function escalateToHuman() {
      window.open('https://line.me/R/ti/p/@sis-freight', '_blank');
    }

    // ═══ KEEP-ALIVE ═══
    function keepAlive() {
      fetch(API_URL + '/health', { method: 'GET' })
        .then(r => r.json())
        .then(() => console.log('[Keep-Alive] OK'))
        .catch(() => console.warn('[Keep-Alive] Backend unreachable'));
    }
    keepAlive();
    setInterval(keepAlive, 14 * 60 * 1000);

    // ═══ MOBILE KEYBOARD FIX ═══
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', onViewportResize);
      window.visualViewport.addEventListener('scroll', onViewportResize);
    }

    function onViewportResize() {
      const chatBox = document.getElementById('chat-box');
      if (!chatBox || !chatBox.classList.contains('open')) return;

      const viewport = window.visualViewport;
      const windowHeight = window.innerHeight;
      const keyboardHeight = windowHeight - viewport.height - viewport.offsetTop;

      if (keyboardHeight > 100) {
        const available = viewport.height - 40;
        chatBox.style.maxHeight = Math.min(available, 450) + 'px';
        setTimeout(() => {
          document.getElementById('chat-input').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 150);
      } else {
        chatBox.style.maxHeight = '';
      }
    }

    // ═══ TRACKING COUNT ═══
    function getOrCreateVisitorId() {
      const storageKey = 'site_visitor_id';
      const existing = localStorage.getItem(storageKey);
      if (existing) return existing;
      const generated = `visitor_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
      localStorage.setItem(storageKey, generated);
      return generated;
    }

    function getOrCreateChatSessionId() {
      const storageKey = 'chat_session_id';
      const existing = sessionStorage.getItem(storageKey);
      if (existing) return existing;
      const generated = `chat_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
      sessionStorage.setItem(storageKey, generated);
      return generated;
    }

    function renderMetrics(data) {
      const visitCountEl = document.getElementById('visit-count');
      const uniqueVisitorCountEl = document.getElementById('unique-visitor-count');
      if (!visitCountEl || !uniqueVisitorCountEl) return;

      visitCountEl.textContent = data.page_views_total.toLocaleString('th-TH');
      uniqueVisitorCountEl.textContent = data.unique_visitors_total.toLocaleString('th-TH');
    }

    function renderMetricsUnavailable() {
      const ids = ['visit-count', 'unique-visitor-count'];
      ids.forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.textContent = '-';
      });
    }

    updateResponseModeUi();

    async function fetchMetrics(endpoint, options = {}) {
      const response = await fetch(API_URL + endpoint, options);
      const data = await response.json().catch(() => ({}));
      if (
        !response.ok ||
        typeof data.page_views_total !== 'number' ||
        typeof data.unique_visitors_total !== 'number'
      ) {
        throw new Error(data.error || `HTTP ${response.status}`);
      }
      return data;
    }

    async function initTracking() {
      try {
        visitorId = getOrCreateVisitorId();
        chatSessionId = getOrCreateChatSessionId();
        const data = await fetchMetrics('/analytics/visit?visitor_id=' + encodeURIComponent(visitorId), { method: 'GET' });
        renderMetrics(data);
      } catch (error) {
        console.warn('Visit counter unavailable:', error);
        renderMetricsUnavailable();
      }
    }
    document.addEventListener('DOMContentLoaded', () => {
      initTracking();
      setChatExpandedState(false);

      const chatToggle = document.getElementById('chat-toggle');
      const chatCloseBtn = document.getElementById('chat-close-btn');
      const chatBackBtn = document.getElementById('chat-back-btn');
      const chatSendBtn = document.getElementById('chat-send-btn');
      const chatInput = document.getElementById('chat-input');

      chatToggle?.addEventListener('click', toggleChat);
      chatCloseBtn?.addEventListener('click', closeChat);
      chatBackBtn?.addEventListener('click', resetChat);
      document.getElementById('chat-mode-quick')?.addEventListener('click', () => setChatResponseMode('quick'));
      document.getElementById('chat-mode-detail')?.addEventListener('click', () => setChatResponseMode('detail'));
      chatSendBtn?.addEventListener('click', sendMessageFromInput);
      chatInput?.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
          event.preventDefault();
          sendMessageFromInput();
        }
      });

      document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && document.getElementById('chat-box')?.classList.contains('open')) {
          closeChat();
        }
      });
    });

