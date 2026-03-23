(function attachFreightChatNetworkUtils(global) {
  function hasVisitorAnalyticsConsent(storageKey = 'freight_pdpa_consent_v1') {
    return localStorage.getItem(storageKey) === 'accepted';
  }

  function setVisitorAnalyticsConsent(accepted, storageKey = 'freight_pdpa_consent_v1') {
    localStorage.setItem(storageKey, accepted ? 'accepted' : 'declined');
  }

  function readChatStream(response, options) {
    const container = options?.container;
    const botMsgDiv = options?.botMsgDiv;
    const renderSafeTextHtml = options?.renderSafeTextHtml || ((text) => text || '');
    const errorPrefix = options?.errorPrefix || 'เกิดข้อผิดพลาด:';
    const noMessageText = options?.noMessageText || 'ไม่พบข้อความตอบกลับจากระบบ';
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullResponse = '';

    function handleLines(lines) {
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const data = line.slice(6);

        if (data === '[DONE]') {
          return true;
        }
        if (data.startsWith('[ERROR]')) {
          const errorText = data.replace('[ERROR]', '').trim() || 'เกิดข้อผิดพลาดในการประมวลผล';
          if (botMsgDiv) {
            botMsgDiv.innerHTML = `<strong>${errorPrefix}</strong><br>${renderSafeTextHtml(errorText)}`;
          }
          fullResponse = `${errorPrefix} ${errorText}`;
          if (container) container.scrollTop = container.scrollHeight;
          return true;
        }

        fullResponse += data;
        if (botMsgDiv) {
          botMsgDiv.innerHTML = renderSafeTextHtml(fullResponse);
        }
        if (container) container.scrollTop = container.scrollHeight;
      }
      return false;
    }

    return (async () => {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        const shouldStop = handleLines(lines);
        if (shouldStop) break;
      }

      if (!fullResponse && botMsgDiv) {
        botMsgDiv.textContent = noMessageText;
      }
      return fullResponse || noMessageText;
    })();
  }

  function getOrCreateVisitorId(storageKey = 'site_visitor_id') {
    if (!hasVisitorAnalyticsConsent()) return '';
    const existing = localStorage.getItem(storageKey);
    if (existing) return existing;
    const generated = `visitor_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
    localStorage.setItem(storageKey, generated);
    return generated;
  }

  function getOrCreateChatSessionId(storageKey = 'chat_session_id') {
    const existing = sessionStorage.getItem(storageKey);
    if (existing) return existing;
    const generated = `chat_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
    sessionStorage.setItem(storageKey, generated);
    return generated;
  }

  function renderMetrics(data, locale = 'th-TH') {
    const visitCountEl = document.getElementById('visit-count');
    const uniqueVisitorCountEl = document.getElementById('unique-visitor-count');
    if (!visitCountEl || !uniqueVisitorCountEl) return;

    visitCountEl.textContent = Number(data.page_views_total || 0).toLocaleString(locale);
    uniqueVisitorCountEl.textContent = Number(data.unique_visitors_total || 0).toLocaleString(locale);
  }

  function renderMetricsUnavailable(ids) {
    (ids || ['visit-count', 'unique-visitor-count']).forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.textContent = '-';
    });
  }

  async function fetchMetrics(options) {
    const apiUrl = options?.apiUrl || '';
    const endpoint = options?.endpoint || '';
    const response = await fetch(apiUrl + endpoint, {
      ...(options?.fetchOptions || {}),
      headers: {
        ...((options?.fetchOptions || {}).headers || {}),
        'X-Visitor-Id': options?.visitorId,
        'X-Session-Id': options?.chatSessionId
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

  async function initTracking(options) {
    try {
      const chatSessionId = options.getOrCreateChatSessionId();
      const consentGranted = typeof options.hasTrackingConsent === 'function'
        ? options.hasTrackingConsent()
        : hasVisitorAnalyticsConsent();
      const visitorId = consentGranted ? options.getOrCreateVisitorId() : '';
      options.setVisitorId(visitorId);
      options.setChatSessionId(chatSessionId);
      if (!consentGranted) {
        options.renderMetricsUnavailable();
        return;
      }
      const data = await options.fetchMetrics('/analytics/visit?visitor_id=' + encodeURIComponent(visitorId), { method: 'GET' });
      options.renderMetrics(data);
    } catch (error) {
      options.reportFrontendError?.('visit_counter_unavailable', error);
      options.renderMetricsUnavailable();
    }
  }

  function startKeepAlive(apiUrl) {
    function keepAlive() {
      fetch(apiUrl + '/health', { method: 'GET' })
        .then((r) => r.json())
        .then(() => console.log('[Keep-Alive] OK'))
        .catch(() => console.warn('[Keep-Alive] Backend unreachable'));
    }
    keepAlive();
    return window.setInterval(keepAlive, 14 * 60 * 1000);
  }

  function bindViewportResize(handler) {
    if (!window.visualViewport || typeof handler !== 'function') return false;
    window.visualViewport.addEventListener('resize', handler);
    window.visualViewport.addEventListener('scroll', handler);
    return true;
  }

  global.FreightChatNetworkUtils = {
    hasVisitorAnalyticsConsent,
    setVisitorAnalyticsConsent,
    readChatStream,
    getOrCreateVisitorId,
    getOrCreateChatSessionId,
    renderMetrics,
    renderMetricsUnavailable,
    fetchMetrics,
    initTracking,
    startKeepAlive,
    bindViewportResize
  };
})(window);
