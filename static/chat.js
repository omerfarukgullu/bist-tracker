function initTickerChat(ticker, labels) {
  labels = labels || {};
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const messages = document.getElementById("chat-messages");
  if (!form || !input || !messages) return;

  function addMessage(text, role) {
    const row = document.createElement("div");
    row.className = `chat-msg ${role}`;
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";
    bubble.textContent = text;
    row.appendChild(bubble);
    messages.appendChild(row);
    messages.scrollTop = messages.scrollHeight;
    return row;
  }

  function ask(question) {
    if (!question.trim()) return;
    addMessage(question, "user");
    const loadingRow = addMessage("...", "bot is-loading");

    fetch(`/hisse/${ticker}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    })
      .then((r) => r.json())
      .then((d) => {
        loadingRow.remove();
        addMessage(d.answer || d.error || (labels.chatError || "Error"), "bot");
      })
      .catch(() => {
        loadingRow.remove();
        addMessage(labels.chatError || "Error", "bot");
      });
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const question = input.value;
    input.value = "";
    ask(question);
  });

  document.querySelectorAll(".chat-chip").forEach((btn) => {
    btn.addEventListener("click", () => ask(btn.dataset.q));
  });
}
