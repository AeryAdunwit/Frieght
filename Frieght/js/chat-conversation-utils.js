(function attachFreightChatConversationUtils(global) {
  function getLastChatTurn(history, role) {
    const items = Array.isArray(history) ? history : [];
    for (let index = items.length - 1; index >= 0; index -= 1) {
      if (items[index]?.role === role) {
        return items[index]?.content || '';
      }
    }
    return '';
  }

  function collectRecentChatText(history) {
    const items = Array.isArray(history) ? history : [];
    return [
      getLastChatTurn(items, 'user'),
      getLastChatTurn(items, 'model'),
      ...items.slice(-6).map((item) => item?.content || '')
    ].filter(Boolean).join('\n');
  }

  function inferConversationMemory(topic, text) {
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

  function buildHandoffSummary(topic, text, inferMemoryFn) {
    const inferMemory = typeof inferMemoryFn === 'function' ? inferMemoryFn : inferConversationMemory;
    const memory = inferMemory(topic, text);
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

    return {
      chips,
      missing: (missingMap[topic] || []).filter(Boolean).slice(0, 3)
    };
  }

  function buildHandoffSeed(options) {
    const topic = options?.topic || '';
    const lastUser = options?.lastUser || '';
    const recentText = options?.recentText || '';
    const fallbackText = options?.userText || lastUser || '';
    const summary = options?.summary || buildHandoffSummary(topic, recentText, options?.inferConversationMemory);
    const jobMatch = recentText.match(/\b\d{6,}\b/);
    const jobNumber = jobMatch ? jobMatch[0] : '';
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
    return fallbackText || 'ต้องการให้ทีมช่วยคุยต่อ';
  }

  function inferCurrentIntentName(activeChatTopic, lastUser) {
    if (activeChatTopic === 'tracking') return 'tracking';
    const source = String(lastUser || '').toLowerCase();
    if (/solar|ธุรกิจ em|hub/.test(source)) return 'solar';
    if (/ราคา|quotation|quote|ค่าส่ง/.test(source)) return 'pricing';
    if (/จอง|booking|เข้ารับ|เหมาคัน|รถใหญ่/.test(source)) return 'booking';
    if (/เคลม|claim|เสียหาย|ส่งผิด/.test(source)) return 'claim';
    if (/เอกสาร/.test(source)) return 'document';
    if (/กี่วัน|ตัดรอบ|ช้า/.test(source)) return 'timeline';
    if (/ทั่วประเทศ|ต่างจังหวัด|พื้นที่/.test(source)) return 'coverage';
    return activeChatTopic || 'general_chat';
  }

  global.FreightChatConversationUtils = {
    getLastChatTurn,
    collectRecentChatText,
    inferConversationMemory,
    inferContactSeed,
    buildHandoffSummary,
    buildHandoffSeed,
    inferCurrentIntentName
  };
})(window);
