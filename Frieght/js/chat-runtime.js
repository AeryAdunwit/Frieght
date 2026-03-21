(function initFreightChatRuntime() {
  const DEFAULT_BACKEND_URL = 'https://frieght-fngh.onrender.com';
  const DEFAULT_PUBLIC_SITE_BASE_URL = 'https://aeryadunwit.github.io/Frieght';
  const CHAT_STATE_STORAGE_KEY = 'freight_chat_state_v1';
  const FRONTEND_ERROR_STORAGE_KEY = document.querySelector('meta[name="app-error-log-key"]')?.getAttribute('content') || 'freight_frontend_errors_v1';
  const FRONTEND_ERROR_MAX = 40;

  function getMetaContent(name, fallback = '') {
    return document.querySelector(`meta[name="${name}"]`)?.getAttribute('content') || fallback;
  }

  function getApiBaseUrl() {
    if (
      window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1' ||
      window.location.protocol === 'file:'
    ) {
      return 'http://localhost:8000';
    }
    return getMetaContent('app-api-base-url', DEFAULT_BACKEND_URL);
  }

  function getPublicSiteBaseUrl() {
    return getMetaContent('app-public-site-base-url', DEFAULT_PUBLIC_SITE_BASE_URL);
  }

  function reportFrontendError(source, error, context = {}) {
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
    const target = document.getElementById('chat-status-live');
    if (!target) return;
    target.textContent = '';
    window.setTimeout(() => {
      target.textContent = message || '';
    }, 0);
  }

  function loadChatState() {
    try {
      return JSON.parse(sessionStorage.getItem(CHAT_STATE_STORAGE_KEY) || 'null');
    } catch (error) {
      reportFrontendError('chat_state_load_failed', error);
      return null;
    }
  }

  function saveChatState(state) {
    try {
      sessionStorage.setItem(CHAT_STATE_STORAGE_KEY, JSON.stringify(state));
      return true;
    } catch (error) {
      reportFrontendError('chat_state_save_failed', error);
      return false;
    }
  }

  window.FreightChatRuntime = Object.freeze({
    defaults: Object.freeze({
      apiBaseUrl: DEFAULT_BACKEND_URL,
      publicSiteBaseUrl: DEFAULT_PUBLIC_SITE_BASE_URL,
      chatStateStorageKey: CHAT_STATE_STORAGE_KEY,
      frontendErrorStorageKey: FRONTEND_ERROR_STORAGE_KEY,
      frontendErrorMax: FRONTEND_ERROR_MAX
    }),
    getMetaContent,
    getApiBaseUrl,
    getPublicSiteBaseUrl,
    reportFrontendError,
    announceToLiveRegion,
    loadChatState,
    saveChatState
  });
})();
