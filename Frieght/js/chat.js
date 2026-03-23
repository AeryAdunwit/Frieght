    // ── CONFIG ──
    const runtime = window.FreightChatRuntime || {};
    const content = window.FreightChatContent || {};
    const stateUtils = window.FreightChatStateUtils || {};
    const renderers = window.FreightChatRenderers || {};
    const messageUtils = window.FreightChatMessageUtils || {};
    const bootUtils = window.FreightChatBootUtils || {};
    const networkUtils = window.FreightChatNetworkUtils || {};
    const DEFAULT_BACKEND_URL = runtime.defaults?.apiBaseUrl || 'https://frieght-fngh.onrender.com';
    const DEFAULT_PUBLIC_SITE_BASE_URL = runtime.defaults?.publicSiteBaseUrl || 'https://aeryadunwit.github.io/Frieght';
    const CHAT_STATE_STORAGE_KEY = runtime.defaults?.chatStateStorageKey || 'freight_chat_state_v1';
    const FRONTEND_ERROR_STORAGE_KEY = runtime.defaults?.frontendErrorStorageKey || document.querySelector('meta[name="app-error-log-key"]')?.getAttribute('content') || 'freight_frontend_errors_v1';
    const FRONTEND_ERROR_MAX = runtime.defaults?.frontendErrorMax || 40;
    
    function getMetaContent(name, fallback = '') {
      if (typeof runtime.getMetaContent === 'function') {
        return runtime.getMetaContent(name, fallback);
      }
      return document.querySelector(`meta[name="${name}"]`)?.getAttribute('content') || fallback;
    }

    function getApiBaseUrl() {
      if (typeof runtime.getApiBaseUrl === 'function') {
        return runtime.getApiBaseUrl();
      }
      if (window.location.hostname === 'localhost' ||
          window.location.hostname === '127.0.0.1' ||
          window.location.protocol === 'file:') {
        return 'http://localhost:8000';
      }
      return getMetaContent('app-api-base-url', DEFAULT_BACKEND_URL);
    }

    const API_URL = getApiBaseUrl();
    const PUBLIC_SITE_BASE_URL = typeof runtime.getPublicSiteBaseUrl === 'function'
      ? runtime.getPublicSiteBaseUrl()
      : getMetaContent('app-public-site-base-url', DEFAULT_PUBLIC_SITE_BASE_URL);
    const PUBLIC_TOOL_LINKS = Object.freeze({
      booking: `${PUBLIC_SITE_BASE_URL}/BookingSolar/`,
      solarHub: 'https://aeryadunwit.github.io/SiSHubEM/',
      tracking: `${PUBLIC_SITE_BASE_URL}/tracking/`,
      skyfrog: `${PUBLIC_SITE_BASE_URL}/tracktrace/`
    });

    // ── STATE ──
    const chatHistory = [];
    let activeChatTopic = null;
    let chatResponseMode = localStorage.getItem('chat_response_mode') === 'detail' ? 'detail' : 'quick';
    let chatUtilityCollapsed = localStorage.getItem('chat_utility_collapsed') === '1';
    let lastChatTrigger = null;
    let visitorId = '';
    let chatSessionId = '';
    const MAX_HISTORY = 20;
    const ESCALATION_TRIGGERS = ['ไม่สามารถ', 'ขออภัย', 'ไม่ทราบ', 'ไม่มีข้อมูล', 'กรุณาติดต่อ', 'แนะนำให้ติดต่อ'];
    const TOPIC_COMPOSER_HINTS = content.TOPIC_COMPOSER_HINTS || {
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
    const RESPONSE_MODE_LABELS = content.RESPONSE_MODE_LABELS || {
      quick: 'ตอบสั้น ตรงประเด็น',
      detail: 'ตอบครบขึ้นอีกนิด อ่านง่าย'
    };
    const TOPIC_SUGGESTIONS = content.TOPIC_SUGGESTIONS || {
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

    function reportFrontendError(source, error, context = {}) {
      if (typeof runtime.reportFrontendError === 'function') {
        runtime.reportFrontendError(source, error, context);
        return;
      }
      try {
        const existing = JSON.parse(localStorage.getItem(FRONTEND_ERROR_STORAGE_KEY) || '[]');
        const entry = {
          source,
          message: String(error?.message || error || 'unknown frontend error'),
          context,
          pathname: window.location.pathname,
          created_at: new Date().toISOString()
        };
        existing.unshift(entry);
        localStorage.setItem(
          FRONTEND_ERROR_STORAGE_KEY,
          JSON.stringify(existing.slice(0, FRONTEND_ERROR_MAX))
        );
      } catch (storageError) {
        console.warn('frontend error buffer unavailable', storageError);
      }
    }

    function announceToLiveRegion(message) {
      if (typeof runtime.announceToLiveRegion === 'function') {
        runtime.announceToLiveRegion(message);
        return;
      }
      if (typeof stateUtils.announceToLiveRegion === 'function') {
        stateUtils.announceToLiveRegion(document.getElementById('chat-status-live'), message);
        return;
      }
      const target = document.getElementById('chat-status-live');
      if (!target) return;
      target.textContent = '';
      window.setTimeout(() => {
        target.textContent = message || '';
      }, 0);
    }

    function getSerializableChatState() {
      if (typeof stateUtils.buildSerializableChatState === 'function') {
        return stateUtils.buildSerializableChatState({
          history: chatHistory,
          maxHistory: MAX_HISTORY,
          activeTopic: activeChatTopic || null,
          responseMode: chatResponseMode,
          utilityCollapsed: chatUtilityCollapsed,
          handoffDraft: {
            name: document.getElementById('handoff-name')?.value || '',
            contact: document.getElementById('handoff-contact')?.value || '',
            channel: document.getElementById('handoff-channel')?.value || 'phone',
            note: document.getElementById('handoff-note')?.value || ''
          }
        });
      }
      return {
        history: chatHistory.slice(-MAX_HISTORY),
        activeTopic: activeChatTopic || null,
        responseMode: chatResponseMode,
        utilityCollapsed: chatUtilityCollapsed,
        handoffDraft: {
          name: document.getElementById('handoff-name')?.value || '',
          contact: document.getElementById('handoff-contact')?.value || '',
          channel: document.getElementById('handoff-channel')?.value || 'phone',
          note: document.getElementById('handoff-note')?.value || ''
        }
      };
    }

    function persistChatState() {
      try {
        if (typeof stateUtils.persistChatState === 'function') {
          stateUtils.persistChatState({
            runtime,
            storageKey: CHAT_STATE_STORAGE_KEY,
            state: getSerializableChatState()
          });
          return;
        }
        if (typeof runtime.saveChatState === 'function') {
          runtime.saveChatState(getSerializableChatState());
        } else {
          sessionStorage.setItem(CHAT_STATE_STORAGE_KEY, JSON.stringify(getSerializableChatState()));
        }
      } catch (error) {
        reportFrontendError('chat_state_persist_failed', error);
      }
    }

    function restoreChatState() {
      try {
        const data = typeof stateUtils.restoreChatState === 'function'
          ? stateUtils.restoreChatState({
              runtime,
              storageKey: CHAT_STATE_STORAGE_KEY
            })
          : (typeof runtime.loadChatState === 'function'
              ? runtime.loadChatState()
              : JSON.parse(sessionStorage.getItem(CHAT_STATE_STORAGE_KEY) || 'null'));
        if (!data) return false;
        const history = Array.isArray(data?.history) ? data.history : [];
        chatHistory.splice(0, chatHistory.length, ...history.filter((item) => item && typeof item.content === 'string'));
        activeChatTopic = typeof data?.activeTopic === 'string' ? data.activeTopic : null;
        chatResponseMode = data?.responseMode === 'detail' ? 'detail' : chatResponseMode;
        chatUtilityCollapsed = data?.utilityCollapsed === true;

        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer && chatHistory.length) {
          messagesContainer.innerHTML = '';
          chatHistory.forEach((item) => {
            appendMessage(item.role === 'user' ? 'user' : 'bot', item.content, false, false);
          });
          document.getElementById('chat-back-btn').style.display = 'block';
        }

        const draft = data?.handoffDraft || {};
        if (document.getElementById('handoff-name')) document.getElementById('handoff-name').value = draft.name || '';
        if (document.getElementById('handoff-contact')) document.getElementById('handoff-contact').value = draft.contact || '';
        if (document.getElementById('handoff-channel')) document.getElementById('handoff-channel').value = draft.channel || 'phone';
        if (document.getElementById('handoff-note')) document.getElementById('handoff-note').value = draft.note || '';

        return chatHistory.length > 0;
      } catch (error) {
        reportFrontendError('chat_state_restore_failed', error);
        return false;
      }
    }

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
      document.querySelectorAll('.content').forEach((el) => el.classList.remove('show'));
      document.querySelectorAll('.tab-btn').forEach((el) => {
        el.classList.remove('active');
        el.setAttribute('aria-selected', 'false');
        el.setAttribute('tabindex', '-1');
      });
      document.getElementById(tab).classList.add('show');
      const matchingButton = Array.from(document.querySelectorAll('.tab-btn'))
        .find(btn => btn.getAttribute('onclick') === `switchTab('${tab}')`);
      if (matchingButton) {
        matchingButton.classList.add('active');
        matchingButton.setAttribute('aria-selected', 'true');
        matchingButton.setAttribute('tabindex', '0');
      }
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
      persistChatState();
    }

    function setChatExpandedState(isOpen) {
      const chatBox = document.getElementById('chat-box');
      const toggleButton = document.getElementById('chat-toggle');
      if (typeof stateUtils.setChatExpandedState === 'function') {
        stateUtils.setChatExpandedState(chatBox, toggleButton, isOpen);
        return;
      }
      chatBox.setAttribute('aria-hidden', String(!isOpen));
      chatBox.setAttribute('aria-modal', String(isOpen));
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
      announceToLiveRegion('เปิดหน้าต่างแชตแล้ว');
      window.setTimeout(() => {
        document.getElementById('chat-input')?.focus();
      }, 0);
    }

    function closeChat() {
      const chatBox = document.getElementById('chat-box');
      chatBox.classList.remove('open');
      setChatExpandedState(false);
      closeHandoffPanel();
      announceToLiveRegion('ปิดหน้าต่างแชตแล้ว');
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
      persistChatState();
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

    function updateChatUtilityUi() {
      const panel = document.getElementById('chat-utility-panel');
      const toggle = document.getElementById('chat-utility-toggle');
      if (!panel || !toggle) return;

      panel.classList.toggle('collapsed', chatUtilityCollapsed);
      toggle.setAttribute('aria-expanded', chatUtilityCollapsed ? 'false' : 'true');
      toggle.textContent = chatUtilityCollapsed ? 'แสดงแถบช่วยคุย' : 'ซ่อนแถบช่วยคุย';
    }

    function setChatUtilityCollapsed(collapsed) {
      chatUtilityCollapsed = !!collapsed;
      localStorage.setItem('chat_utility_collapsed', chatUtilityCollapsed ? '1' : '0');
      updateChatUtilityUi();
      persistChatState();
    }

    function toggleChatUtility() {
      setChatUtilityCollapsed(!chatUtilityCollapsed);
    }

    function setChatResponseMode(mode) {
      chatResponseMode = mode === 'detail' ? 'detail' : 'quick';
      localStorage.setItem('chat_response_mode', chatResponseMode);
      updateResponseModeUi();
      persistChatState();
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
      messagesContainer.innerHTML = typeof content.renderWelcomeCardHtml === 'function'
        ? content.renderWelcomeCardHtml()
        : `
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

      const link = PUBLIC_TOOL_LINKS.booking;
      appendMessage("bot", `งานเหมาคันหรือของชิ้นใหญ่ กดหน้าจองต่อได้เลยค้าบ<br><br><a href="${link}" target="_blank" style="display: inline-block; background: var(--primary); color: white; padding: 10px 20px; border-radius: 999px; text-decoration: none; font-weight: bold; margin-top: 5px;"><i class="fas fa-external-link-alt"></i> เปิดหน้าจองงาน</a>`, true);

      const container = document.getElementById('chat-messages');
      const followupDiv = document.createElement('div');
      followupDiv.className = 'message bot';
      followupDiv.innerHTML = typeof renderers.renderBookingFollowupHtml === 'function'
        ? renderers.renderBookingFollowupHtml()
        : `
          <p style="margin-bottom: 10px;">อยากได้สรุปขั้นตอนต่อไหมค้าบ</p>
          <div style="display: flex; gap: 10px;">
            <button class="quick-btn" style="flex:1; text-align:center; justify-content:center;" onclick="handleBookingFollowup(true)">สรุปขั้นตอน</button>
            <button class="quick-btn" style="flex:1; text-align:center; justify-content:center;" onclick="handleBookingFollowup(false)">ไว้ก่อนน้า</button>
          </div>
        `;
      container.appendChild(followupDiv);
      container.scrollTop = container.scrollHeight;
    };

    handleSolarHubAction = function() {
      const card = document.getElementById('welcome-card');
      if (card) card.remove();
      document.getElementById('chat-back-btn').style.display = 'block';
      activeChatTopic = 'solar';
      updateComposerState('solar');

      const link = PUBLIC_TOOL_LINKS.solarHub;
      appendMessage(
        "bot",
        `เปิดหน้าส่ง Solar ผ่าน Hub ให้แล้วค้าบ<br><br><a href="${link}" target="_blank" rel="noopener noreferrer" style="display: inline-block; background: var(--primary); color: white; padding: 10px 20px; border-radius: 999px; text-decoration: none; font-weight: bold; margin-top: 5px;"><i class="fas fa-external-link-alt"></i> เปิด SiS Hub EM</a><br><br><strong>วิธีใช้งาน</strong><br>1. ใส่ต้นทาง และปลายทาง<br>2. ตรวจข้อมูลแล้วกดดำเนินการต่อได้เลยค้าบ`,
        true
      );
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

    const isLikelyTrackingCode = typeof messageUtils.isLikelyTrackingCode === 'function'
      ? messageUtils.isLikelyTrackingCode
      : (text) => /\d+/.test(text || '');
    const escapeHtml = typeof messageUtils.escapeHtml === 'function'
      ? messageUtils.escapeHtml
      : (text) => String(text || '');
    const stripInternalSystemData = typeof messageUtils.stripInternalSystemData === 'function'
      ? messageUtils.stripInternalSystemData
      : (text) => String(text || '');
    const sanitizeUrl = typeof messageUtils.sanitizeUrl === 'function'
      ? messageUtils.sanitizeUrl
      : (url) => url || '';
    const renderSafeTextHtml = typeof messageUtils.renderSafeTextHtml === 'function'
      ? messageUtils.renderSafeTextHtml
      : (text) => escapeHtml(text || '');
    const getTrackingSmallTalkReply = typeof messageUtils.getTrackingSmallTalkReply === 'function'
      ? messageUtils.getTrackingSmallTalkReply
      : () => null;
    const extractTrackingLinkData = (text) => typeof messageUtils.extractTrackingLinkData === 'function'
      ? messageUtils.extractTrackingLinkData(text, PUBLIC_TOOL_LINKS)
      : null;
    const openTrackingRedirect = typeof messageUtils.openTrackingRedirect === 'function'
      ? messageUtils.openTrackingRedirect
      : (() => {});
    const renderTrackingCard = (text) => typeof messageUtils.renderTrackingCard === 'function'
      ? messageUtils.renderTrackingCard(text, PUBLIC_TOOL_LINKS)
      : null;
    const createFeedbackActions = (userText, botText) => typeof messageUtils.createFeedbackActions === 'function'
      ? messageUtils.createFeedbackActions({ userText, botText, apiUrl: API_URL, chatSessionId, visitorId })
      : document.createElement('div');
    const conversationUtils = window.FreightChatConversationUtils || {};

    function getLastChatTurn(role) {
      if (typeof conversationUtils.getLastChatTurn === 'function') {
        return conversationUtils.getLastChatTurn(chatHistory, role);
      }
      for (let index = chatHistory.length - 1; index >= 0; index -= 1) {
        if (chatHistory[index]?.role === role) {
          return chatHistory[index]?.content || '';
        }
      }
      return '';
    }

    function collectRecentChatText() {
      if (typeof conversationUtils.collectRecentChatText === 'function') {
        return conversationUtils.collectRecentChatText(chatHistory);
      }
      return [
        getLastChatTurn('user'),
        getLastChatTurn('model'),
        ...chatHistory.slice(-6).map(item => item?.content || '')
      ].filter(Boolean).join('\n');
    }

    function inferConversationMemory(topic, text = '') {
      if (typeof conversationUtils.inferConversationMemory === 'function') {
        return conversationUtils.inferConversationMemory(topic, text);
      }
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
      if (typeof conversationUtils.inferContactSeed === 'function') {
        return conversationUtils.inferContactSeed(text);
      }
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
      if (typeof conversationUtils.buildHandoffSeed === 'function') {
        return conversationUtils.buildHandoffSeed({
          topic,
          userText,
          lastUser: userText || getLastChatTurn('user') || '',
          recentText: collectRecentChatText(),
          summary: buildHandoffSummary(topic),
          inferConversationMemory
        });
      }
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
      if (typeof conversationUtils.buildHandoffSummary === 'function') {
        return conversationUtils.buildHandoffSummary(topic, collectRecentChatText(), inferConversationMemory);
      }
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
        target.hidden = true;
        target.innerHTML = '';
        return;
      }
      target.hidden = false;
      target.style.display = 'flex';
      const note = missing.length
        ? `ยังขาดอีกนิดค้าบ: ${missing.join(', ')}`
        : 'ข้อมูลหลักเริ่มครบแล้วค้าบ ทีมหยิบไปคุยต่อได้ไวขึ้น';
      target.innerHTML = typeof renderers.renderHandoffSummaryHtml === 'function'
        ? renderers.renderHandoffSummaryHtml(chips, note)
        : `
          <div class="handoff-summary-title">ข้อมูลที่น้องจับได้จากแชตนี้</div>
          ${chips.length ? `<div class="handoff-summary-list">${chips.map((chip) => `<span class="handoff-summary-chip">${escapeHtml(chip)}</span>`).join('')}</div>` : ''}
          <div class="handoff-summary-note">${escapeHtml(note)}</div>
        `;
    }

    function renderIntakeCoach(topic = activeChatTopic || inferCurrentIntentName()) {
      const target = document.getElementById('chat-intake-coach');
      if (!target) return;
      const normalizedTopic = normalizeSuggestionTopic(topic);
      const supportedTopics = ['solar', 'pricing', 'booking', 'claim', 'tracking'];
      if (!supportedTopics.includes(normalizedTopic)) {
        target.hidden = true;
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
        ? 'ข้อมูลเริ่มครบแล้วค้าบ'
        : `ตอนนี้ยังขาด: ${missing.join(', ')}`;
      target.hidden = false;
      target.style.display = 'flex';
      target.innerHTML = typeof renderers.renderIntakeCoachHtml === 'function'
        ? renderers.renderIntakeCoachHtml({
            title: titleMap[normalizedTopic] || 'เช็กข้อมูลงาน',
            line,
            ready,
            chips
          })
        : `
          <div class="chat-intake-head">
            <div class="chat-intake-title">${escapeHtml(titleMap[normalizedTopic] || 'เช็กข้อมูลงาน')}</div>
            <span class="chat-intake-badge ${ready ? 'ready' : ''}">${ready ? 'พร้อมส่งต่อ' : 'ยังไม่ครบ'}</span>
          </div>
          <div class="chat-intake-line">${escapeHtml(line)}</div>
          ${chips.length ? `<div class="chat-intake-list">${chips.map((chip) => `<span class="chat-intake-chip">${escapeHtml(chip)}</span>`).join('')}</div>` : ''}
        `;
    }

    function inferCurrentIntentName() {
      if (typeof conversationUtils.inferCurrentIntentName === 'function') {
        return conversationUtils.inferCurrentIntentName(activeChatTopic, getLastChatTurn('user'));
      }
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
      persistChatState();
      announceToLiveRegion('เปิดฟอร์มส่งต่อให้ทีมแล้ว');
      (contactEl.value.trim() ? note : contactEl).focus();
    }

    function closeHandoffPanel() {
      const panel = document.getElementById('handoff-panel');
      if (panel) {
        panel.classList.remove('open');
      }
      persistChatState();
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
          headers: {
            'Content-Type': 'application/json',
            'X-Session-Id': chatSessionId,
            'X-Visitor-Id': visitorId
          },
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
        persistChatState();
        announceToLiveRegion('ส่งข้อมูลให้ทีมเรียบร้อยแล้ว');
        submitBtn.textContent = 'ส่งแล้วค้าบ';
        setTimeout(() => {
          submitBtn.disabled = false;
          submitBtn.textContent = 'ส่งให้ทีมต่อ';
        }, 1500);
      } catch (error) {
        reportFrontendError('handoff_submit_failed', error, { sessionId: chatSessionId });
        statusEl.textContent = 'ส่งต่อให้ทีมยังไม่สำเร็จ ลองใหม่ได้ค้าบ';
        submitBtn.disabled = false;
      }
    }

    function appendMessage(role, text, isHTML = false, persist = true) {
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
      if (persist) persistChatState();
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
        chatHistory.push({ role: "user", content: userText });
        appendMessage("user", userText);
        chatHistory.push({ role: "model", content: trackingSmallTalkReply });
        appendMessage("bot", trackingSmallTalkReply);
        renderChatSuggestions('tracking', userText, trackingSmallTalkReply);
        renderIntakeCoach('tracking');
        renderHandoffSummary();
        persistChatState();
        clearTimeout(timer);
        return;
      }

      chatHistory.push({ role: "user", content: userText });
      persistChatState();
      appendMessage("user", userText);
      showTypingIndicator();

      try {
        const res = await fetch(API_URL + '/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Session-Id': chatSessionId,
            'X-Visitor-Id': visitorId
          },
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
            appendMessage("bot", "ตอนนี้มีปัญหานิดหน่อย ลองใหม่อีกครั้งได้เลยค้าบ");
            reportFrontendError('chat_http_error', data.error || `HTTP ${res.status}`, { status: res.status });
          }
          chatHistory.pop();
          persistChatState();
          return;
        }

        const container = document.getElementById('chat-messages');
        const botMsgDiv = document.createElement('div');
        botMsgDiv.className = 'message bot';
        container.appendChild(botMsgDiv);
        let fullResponse = typeof networkUtils.readChatStream === 'function'
          ? await networkUtils.readChatStream(res, {
              container,
              botMsgDiv,
              renderSafeTextHtml,
              errorPrefix: 'เกิดข้อผิดพลาด:',
              noMessageText: 'ไม่พบข้อความตอบกลับจากระบบ'
            })
          : '';

        if (!fullResponse) {
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
        }

        fullResponse = stripInternalSystemData(fullResponse);

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
        persistChatState();
      } catch (err) {
        hideTypingIndicator();
        if (err.name === 'AbortError') {
          appendMessage("bot", "ระบบใช้เวลาตอบนานเกินไป กรุณาลองอีกครั้ง");
        } else {
          appendMessage("bot", "ตอนนี้เชื่อมต่อไม่สำเร็จ ลองใหม่อีกครั้งได้เลยค้าบ");
          reportFrontendError('chat_fetch_failed', err, { sessionId: chatSessionId });
        }
        chatHistory.pop();
        persistChatState();
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
      if (typeof networkUtils.startKeepAlive === 'function') {
        return;
      }
      fetch(API_URL + '/health', { method: 'GET' })
        .then(r => r.json())
        .then(() => console.log('[Keep-Alive] OK'))
        .catch(() => console.warn('[Keep-Alive] Backend unreachable'));
    }
    if (typeof networkUtils.startKeepAlive === 'function') {
      networkUtils.startKeepAlive(API_URL);
    } else {
      keepAlive();
      setInterval(keepAlive, 14 * 60 * 1000);
    }

    // ═══ MOBILE KEYBOARD FIX ═══
    if (typeof networkUtils.bindViewportResize === 'function') {
      networkUtils.bindViewportResize(onViewportResize);
    } else if (window.visualViewport) {
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
      if (typeof networkUtils.getOrCreateVisitorId === 'function') {
        return networkUtils.getOrCreateVisitorId();
      }
      const storageKey = 'site_visitor_id';
      const existing = localStorage.getItem(storageKey);
      if (existing) return existing;
      const generated = `visitor_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
      localStorage.setItem(storageKey, generated);
      return generated;
    }

    function getOrCreateChatSessionId() {
      if (typeof networkUtils.getOrCreateChatSessionId === 'function') {
        return networkUtils.getOrCreateChatSessionId();
      }
      const storageKey = 'chat_session_id';
      const existing = sessionStorage.getItem(storageKey);
      if (existing) return existing;
      const generated = `chat_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
      sessionStorage.setItem(storageKey, generated);
      return generated;
    }

    function renderMetrics(data) {
      if (typeof networkUtils.renderMetrics === 'function') {
        networkUtils.renderMetrics(data, 'th-TH');
        return;
      }
      const visitCountEl = document.getElementById('visit-count');
      const uniqueVisitorCountEl = document.getElementById('unique-visitor-count');
      if (!visitCountEl || !uniqueVisitorCountEl) return;

      visitCountEl.textContent = data.page_views_total.toLocaleString('th-TH');
      uniqueVisitorCountEl.textContent = data.unique_visitors_total.toLocaleString('th-TH');
    }

    function renderMetricsUnavailable() {
      if (typeof networkUtils.renderMetricsUnavailable === 'function') {
        networkUtils.renderMetricsUnavailable(['visit-count', 'unique-visitor-count']);
        return;
      }
      const ids = ['visit-count', 'unique-visitor-count'];
      ids.forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.textContent = '-';
      });
    }

    updateResponseModeUi();
    updateChatUtilityUi();

    async function fetchMetrics(endpoint, options = {}) {
      if (typeof networkUtils.fetchMetrics === 'function') {
        return networkUtils.fetchMetrics({
          apiUrl: API_URL,
          endpoint,
          fetchOptions: options,
          visitorId: visitorId || getOrCreateVisitorId(),
          chatSessionId: chatSessionId || getOrCreateChatSessionId()
        });
      }
      const response = await fetch(API_URL + endpoint, {
        ...options,
        headers: {
          ...(options.headers || {}),
          'X-Visitor-Id': visitorId || getOrCreateVisitorId(),
          'X-Session-Id': chatSessionId || getOrCreateChatSessionId()
        }
      });
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
      if (typeof networkUtils.initTracking === 'function') {
        return networkUtils.initTracking({
          getOrCreateVisitorId,
          getOrCreateChatSessionId,
          setVisitorId: (value) => { visitorId = value; },
          setChatSessionId: (value) => { chatSessionId = value; },
          fetchMetrics,
          renderMetrics,
          renderMetricsUnavailable,
          reportFrontendError
        });
      }
      try {
        chatSessionId = getOrCreateChatSessionId();
        visitorId = getOrCreateVisitorId();
        const data = await fetchMetrics('/analytics/visit?visitor_id=' + encodeURIComponent(visitorId), { method: 'GET' });
        renderMetrics(data);
      } catch (error) {
        console.warn('Visit counter unavailable:', error);
        reportFrontendError('visit_counter_unavailable', error);
        renderMetricsUnavailable();
      }
    }

    function bindChatDraftPersistence() {
      if (typeof bootUtils.bindChatDraftPersistence === 'function') {
        bootUtils.bindChatDraftPersistence(persistChatState);
        return;
      }
      ['handoff-name', 'handoff-contact', 'handoff-note'].forEach((id) => {
        document.getElementById(id)?.addEventListener('input', persistChatState);
      });
      document.getElementById('handoff-channel')?.addEventListener('change', persistChatState);
    }

    function bindTabKeyboardNavigation() {
      if (typeof bootUtils.bindTabKeyboardNavigation === 'function') {
        bootUtils.bindTabKeyboardNavigation();
        return;
      }
      const tabs = Array.from(document.querySelectorAll('.tab-btn'));
      if (!tabs.length) return;
      tabs.forEach((tab, index) => {
        tab.addEventListener('keydown', (event) => {
          if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
          event.preventDefault();
          let nextIndex = index;
          if (event.key === 'ArrowRight') nextIndex = (index + 1) % tabs.length;
          if (event.key === 'ArrowLeft') nextIndex = (index - 1 + tabs.length) % tabs.length;
          if (event.key === 'Home') nextIndex = 0;
          if (event.key === 'End') nextIndex = tabs.length - 1;
          tabs[nextIndex].focus();
          tabs[nextIndex].click();
        });
      });
    }

    function bindFrontendErrorTracking() {
      if (typeof bootUtils.bindFrontendErrorTracking === 'function') {
        bootUtils.bindFrontendErrorTracking(reportFrontendError);
        return;
      }
      window.addEventListener('error', (event) => {
        reportFrontendError('window_error', event.error || event.message, {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno
        });
      });
      window.addEventListener('unhandledrejection', (event) => {
        reportFrontendError('unhandled_rejection', event.reason);
      });
    }

    function normalizeChatMarkup() {
      if (typeof bootUtils.normalizeChatMarkup === 'function') {
        bootUtils.normalizeChatMarkup();
        return;
      }
      const headerActions = document.querySelector('#chat-header > div');
      const backButton = document.getElementById('chat-back-btn');
      const closeButton = document.getElementById('chat-close-btn');
      const handoffCloseButton = document.querySelector('#handoff-panel .handoff-head button');

      headerActions?.classList.add('chat-header-actions');
      backButton?.classList.add('chat-header-icon-btn', 'chat-back-btn');
      closeButton?.classList.add('chat-header-icon-btn');
      handoffCloseButton?.classList.add('handoff-close-btn');

      headerActions?.removeAttribute('style');
      closeButton?.removeAttribute('style');
      handoffCloseButton?.removeAttribute('style');
    }

    document.addEventListener('DOMContentLoaded', () => {
      if (typeof bootUtils.initializeChatBoot === 'function') {
        bootUtils.initializeChatBoot({
          initTracking,
          setChatExpandedState,
          reportFrontendError,
          persistChatState,
          restoreChatState,
          updateResponseModeUi,
          updateChatUtilityUi,
          updateComposerState,
          renderHandoffSummary,
          showWelcomeMessage,
          getActiveTopic: () => activeChatTopic,
          toggleChat,
          closeChat,
          resetChat,
          setChatResponseMode,
          toggleChatUtility,
          sendMessageFromInput
        });
        return;
      }
      initTracking();
      setChatExpandedState(false);
      bindFrontendErrorTracking();
      bindTabKeyboardNavigation();
      bindChatDraftPersistence();
      normalizeChatMarkup();

      const chatToggle = document.getElementById('chat-toggle');
      const chatCloseBtn = document.getElementById('chat-close-btn');
      const chatBackBtn = document.getElementById('chat-back-btn');
      const chatSendBtn = document.getElementById('chat-send-btn');
      const chatInput = document.getElementById('chat-input');

      const restored = restoreChatState();
      updateResponseModeUi();
      updateChatUtilityUi();
      updateComposerState(activeChatTopic || 'general');
      renderHandoffSummary();
      if (!restored) {
        showWelcomeMessage();
      }

      chatToggle?.addEventListener('click', toggleChat);
      chatCloseBtn?.addEventListener('click', closeChat);
      chatBackBtn?.addEventListener('click', resetChat);
      document.getElementById('chat-mode-quick')?.addEventListener('click', () => setChatResponseMode('quick'));
      document.getElementById('chat-mode-detail')?.addEventListener('click', () => setChatResponseMode('detail'));
      document.getElementById('chat-utility-toggle')?.addEventListener('click', toggleChatUtility);
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



