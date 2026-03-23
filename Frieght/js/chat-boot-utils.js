(function attachFreightChatBootUtils(global) {
  function bindChatDraftPersistence(persistFn) {
    ['handoff-name', 'handoff-contact', 'handoff-note'].forEach((id) => {
      document.getElementById(id)?.addEventListener('input', persistFn);
    });
    document.getElementById('handoff-channel')?.addEventListener('change', persistFn);
  }

  function bindTabKeyboardNavigation() {
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

  function bindFrontendErrorTracking(reportFn) {
    window.addEventListener('error', (event) => {
      reportFn('window_error', event.error || event.message, {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
      });
    });
    window.addEventListener('unhandledrejection', (event) => {
      reportFn('unhandled_rejection', event.reason);
    });
  }

  function normalizeChatMarkup() {
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

  function bindChatUiEvents(options) {
    const chatToggle = document.getElementById('chat-toggle');
    const chatCloseBtn = document.getElementById('chat-close-btn');
    const chatBackBtn = document.getElementById('chat-back-btn');
    const chatSendBtn = document.getElementById('chat-send-btn');
    const chatInput = document.getElementById('chat-input');

    chatToggle?.addEventListener('click', options.toggleChat);
    chatCloseBtn?.addEventListener('click', options.closeChat);
    chatBackBtn?.addEventListener('click', options.resetChat);
    document.getElementById('chat-mode-quick')?.addEventListener('click', () => options.setChatResponseMode('quick'));
    document.getElementById('chat-mode-detail')?.addEventListener('click', () => options.setChatResponseMode('detail'));
    document.getElementById('chat-utility-toggle')?.addEventListener('click', options.toggleChatUtility);
    chatSendBtn?.addEventListener('click', options.sendMessageFromInput);
    chatInput?.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        options.sendMessageFromInput();
      }
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && document.getElementById('chat-box')?.classList.contains('open')) {
        options.closeChat();
      }
    });
  }

  function initializeChatBoot(options) {
    options.initializeConsentBanner?.();
    options.initTracking();
    options.setChatExpandedState(false);
    bindFrontendErrorTracking(options.reportFrontendError);
    bindTabKeyboardNavigation();
    bindChatDraftPersistence(options.persistChatState);
    normalizeChatMarkup();

    const restored = options.restoreChatState();
    options.updateResponseModeUi();
    options.updateChatUtilityUi();
    const activeTopic = typeof options.getActiveTopic === 'function'
      ? options.getActiveTopic()
      : options.activeTopic;
    options.updateComposerState(activeTopic || 'general');
    options.renderHandoffSummary();
    if (!restored) {
      options.showWelcomeMessage();
    }

    bindChatUiEvents(options);
  }

  global.FreightChatBootUtils = {
    bindChatDraftPersistence,
    bindTabKeyboardNavigation,
    bindFrontendErrorTracking,
    normalizeChatMarkup,
    bindChatUiEvents,
    initializeChatBoot
  };
})(window);
