(function attachFreightChatStateUtils(global) {
  function announceToLiveRegion(target, message) {
    if (!target) return;
    target.textContent = '';
    window.setTimeout(() => {
      target.textContent = message || '';
    }, 0);
  }

  function buildSerializableChatState(options) {
    const history = Array.isArray(options?.history) ? options.history : [];
    const maxHistory = Number.isFinite(options?.maxHistory) ? options.maxHistory : 20;
    const handoffDraft = options?.handoffDraft || {};
    return {
      history: history.slice(-maxHistory),
      activeTopic: options?.activeTopic || null,
      responseMode: options?.responseMode || 'quick',
      utilityCollapsed: options?.utilityCollapsed === true,
      handoffDraft: {
        name: handoffDraft.name || '',
        contact: handoffDraft.contact || '',
        channel: handoffDraft.channel || 'phone',
        note: handoffDraft.note || ''
      }
    };
  }

  function persistChatState(options) {
    const runtime = options?.runtime || {};
    const storageKey = options?.storageKey || 'freight_chat_state_v1';
    const state = options?.state || {};

    if (typeof runtime.saveChatState === 'function') {
      runtime.saveChatState(state);
      return;
    }
    sessionStorage.setItem(storageKey, JSON.stringify(state));
  }

  function restoreChatState(options) {
    const runtime = options?.runtime || {};
    const storageKey = options?.storageKey || 'freight_chat_state_v1';
    if (typeof runtime.loadChatState === 'function') {
      return runtime.loadChatState();
    }
    return JSON.parse(sessionStorage.getItem(storageKey) || 'null');
  }

  function setChatExpandedState(chatBox, toggleButton, isOpen) {
    if (chatBox) {
      chatBox.setAttribute('aria-hidden', String(!isOpen));
      chatBox.setAttribute('aria-modal', String(isOpen));
    }
    if (toggleButton) {
      toggleButton.setAttribute('aria-expanded', String(isOpen));
    }
  }

  global.FreightChatStateUtils = {
    announceToLiveRegion,
    buildSerializableChatState,
    persistChatState,
    restoreChatState,
    setChatExpandedState
  };
})(window);
