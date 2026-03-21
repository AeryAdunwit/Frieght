const metaApiBase = document.querySelector('meta[name="api-base-url"]')?.content?.trim();
const API_BASE =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
    ? "http://localhost:8000"
    : (metaApiBase || "https://YOUR-RENDER-APP.onrender.com");

const ESCALATION_TRIGGERS = [
  "ขออภัย",
  "ไม่พบข้อมูล",
  "กรุณาติดต่อทีมงาน",
  "ติดต่อทีมงานโดยตรง",
];

const history = [];
const maxTurns = 12;

const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const sendButton = document.getElementById("send-button");
const resetButton = document.getElementById("reset-chat");
const escalationBar = document.getElementById("escalation-bar");

function appendMessage(role, text, extraClass = "") {
  const article = document.createElement("article");
  article.className = `message ${role} ${extraClass}`.trim();
  article.innerHTML = formatMessage(text);
  chatMessages.appendChild(article);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return article;
}

function formatMessage(text) {
  return escapeHtml(text)
    .replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noreferrer">$1</a>')
    .replace(/\n/g, "<br>");
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function setEscalation(text) {
  const shouldShow = ESCALATION_TRIGGERS.some((keyword) => text.includes(keyword));
  escalationBar.hidden = !shouldShow;
}

function trimHistory() {
  if (history.length > maxTurns) {
    history.splice(0, history.length - maxTurns);
  }
}

function resetChat() {
  history.length = 0;
  chatMessages.innerHTML = "";
  escalationBar.hidden = true;
  appendMessage(
    "bot",
    "สวัสดีครับ ฉันช่วยตอบคำถามจากฐานความรู้ และช่วยเช็คสถานะงานที่มีเลข 10 หลักได้ครับ"
  );
}

function autoGrowTextarea() {
  chatInput.style.height = "auto";
  chatInput.style.height = `${Math.min(chatInput.scrollHeight, 180)}px`;
}

async function sendMessage(message) {
  history.push({ role: "user", content: message });
  trimHistory();

  appendMessage("user", message);
  const typingMessage = appendMessage("bot", "กำลังพิมพ์...", "typing");

  sendButton.disabled = true;
  chatInput.disabled = true;

  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        history: history.filter((turn, index) => index < history.length - 1),
      }),
    });

    if (!response.ok) {
      typingMessage.remove();
      const data = await response.json().catch(() => ({}));
      const errorText =
        response.status === 429
          ? "ส่งข้อความถี่เกินไป กรุณารอสักครู่แล้วลองใหม่ครับ"
          : data.error || "เกิดข้อผิดพลาดในการเชื่อมต่อระบบ";
      appendMessage("bot", errorText);
      history.pop();
      setEscalation(errorText);
      return;
    }

    typingMessage.classList.remove("typing");
    let fullResponse = "";
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) {
          continue;
        }

        const payload = line.slice(6);
        if (payload === "[DONE]") {
          break;
        }
        if (payload.startsWith("[ERROR]")) {
          fullResponse = "เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้งครับ";
          typingMessage.innerHTML = formatMessage(fullResponse);
          break;
        }

        fullResponse += payload;
        typingMessage.innerHTML = formatMessage(fullResponse);
        chatMessages.scrollTop = chatMessages.scrollHeight;
      }
    }

    if (!fullResponse) {
      fullResponse = "ไม่พบข้อความตอบกลับจากระบบ กรุณาลองใหม่อีกครั้งครับ";
      typingMessage.innerHTML = formatMessage(fullResponse);
    }

    history.push({ role: "model", content: fullResponse });
    trimHistory();
    setEscalation(fullResponse);
  } catch (error) {
    typingMessage.remove();
    history.pop();
    const fallbackMessage = "ไม่สามารถเชื่อมต่อ backend ได้ในขณะนี้ กรุณาลองใหม่อีกครั้งครับ";
    appendMessage("bot", fallbackMessage);
    setEscalation(fallbackMessage);
  } finally {
    sendButton.disabled = false;
    chatInput.disabled = false;
    chatInput.focus();
  }
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) {
    return;
  }

  chatInput.value = "";
  autoGrowTextarea();
  await sendMessage(message);
});

chatInput.addEventListener("input", autoGrowTextarea);
chatInput.addEventListener("keydown", async (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    if (!chatInput.value.trim()) {
      return;
    }
    chatForm.requestSubmit();
  }
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", async () => {
    const prompt = button.getAttribute("data-prompt");
    if (!prompt) {
      return;
    }
    chatInput.value = "";
    autoGrowTextarea();
    await sendMessage(prompt);
  });
});

resetButton.addEventListener("click", resetChat);

async function keepAlive() {
  try {
    await fetch(`${API_BASE}/health`);
  } catch (error) {
    console.warn("[keep-alive] backend unreachable");
  }
}

resetChat();
keepAlive();
setInterval(keepAlive, 5 * 60 * 1000);
