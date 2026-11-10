// ClearCart assistant page: typed chat, optional voice in/out, PIN confirmation.
(function () {
  "use strict";
  const log = document.getElementById("log");
  const chatForm = document.getElementById("chat-form");
  const msg = document.getElementById("msg");
  const speakBox = document.getElementById("speak");
  const micBtn = document.getElementById("mic");
  const voiceNote = document.getElementById("voice-note");
  const confirmBox = document.getElementById("confirm");
  const confirmH = document.getElementById("confirm-h");
  const readback = document.getElementById("readback");
  const confirmSub = document.getElementById("confirm-sub");
  const pinSubmit = document.getElementById("pin-submit");
  const meter = document.getElementById("confirm-meter");
  const meterText = document.getElementById("confirm-meter-text");
  const meterBar = document.getElementById("confirm-meter-bar");
  const pinForm = document.getElementById("pin-form");
  const pin = document.getElementById("pin");
  const cancelBtn = document.getElementById("cancel");
  const unlockBox = document.getElementById("unlock");
  const unlockH = document.getElementById("unlock-h");
  const unlockForm = document.getElementById("unlock-form");
  const unlockPin = document.getElementById("unlock-pin");
  const history = [];
  let busy = false;
  // Basket the mascot shows how things are going. Purely visual: every state is also said in text.
  let moodTimer = null;
  function mood(m, ms) {
    clearTimeout(moodTimer);
    document.documentElement.dataset.mood = m;
    if (ms) moodTimer = setTimeout(() => { document.documentElement.dataset.mood = "idle"; }, ms);
  }
  function resync() { if (window.ccPinSync) { window.ccPinSync(pin); window.ccPinSync(unlockPin); } }

  // ---- Remembered setting (per browser only) ----
  try { speakBox.checked = localStorage.getItem("cc-speak") === "1"; } catch (e) {}
  speakBox.addEventListener("change", () => {
    try { localStorage.setItem("cc-speak", speakBox.checked ? "1" : "0"); } catch (e) {}
    if (!speakBox.checked && window.speechSynthesis) window.speechSynthesis.cancel();
  });

  function add(who, text) {
    const p = document.createElement("p");
    p.className = "msg " + (who === "you" ? "you" : "bot");
    const label = document.createElement("span");
    label.className = "who";
    label.textContent = who === "you" ? "You" : "ClearCart";
    const colon = document.createElement("span");
    colon.className = "sr-only";
    colon.textContent = ":";
    label.appendChild(colon);
    p.appendChild(label);
    p.appendChild(document.createTextNode(" " + text));
    log.appendChild(p);
    p.scrollIntoView({ block: "nearest" });
  }

  function say(text) {
    if (!speakBox.checked || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "en-GB";
    u.rate = 1;
    window.speechSynthesis.speak(u);
  }

  function reply(text) {
    add("bot", text);
    say(text);
    history.push({ role: "assistant", text: text });
  }

  function applyState(data) {
    if (data.redirect) { window.location.href = data.redirect; return; }
    if (data.locked) {
      mood("sleepy");
      unlockBox.hidden = false;
      confirmBox.hidden = true;
      unlockPin.value = "";
      resync();
      unlockH.focus();
      return;
    }
    unlockBox.hidden = true;
    if (data.pending) {
      mood(data.ok === false ? "worried" : "excited");
      const p = data.pending;
      const refund = p.type === "refund";
      readback.textContent = p.readback;
      confirmH.textContent = p.amount ? (refund ? "Refund " : "Pay ") + p.amount
        : (refund ? "Check before you confirm the refund" : "Check before you pay");
      confirmSub.textContent = refund ? "Nothing has been refunded yet." : "Nothing has been charged yet.";
      confirmSub.hidden = /Nothing has been/i.test(p.readback);  // the read-back already says it
      pinSubmit.textContent = (refund ? "Refund" : "Pay") + (p.amount ? " " + p.amount : "");
      log.scrollTop = log.scrollHeight;
      if (!refund && p.amount && p.limit) {
        meterText.textContent = p.amount + " of your " + p.limit + " limit";
        meterBar.style.width = p.share + "%";
        meter.hidden = false;
      } else {
        meter.hidden = true;
      }
      confirmBox.hidden = false;
      pin.value = "";
      resync();
      pin.focus();
    } else {
      confirmBox.hidden = true;
      if (data.ok === true) mood("happy", 6000);
      else if (data.ok === false) mood("worried", 5000);
      else if (document.documentElement.dataset.mood !== "happy") mood("idle");
    }
  }

  async function post(url, body) {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
      credentials: "same-origin",
    });
    return r.json();
  }

  async function send(text) {
    if (busy || !text) return;
    busy = true;
    add("you", text);
    const sentHistory = history.slice(-10);
    history.push({ role: "user", text: text });
    msg.value = "";
    mood("thinking");
    try {
      const data = await post("/api/chat", { message: text, history: sentHistory });
      reply(data.reply || "Sorry, something went wrong.");
      applyState(data);
    } catch (e) {
      reply("Sorry, I couldn't reach ClearCart. Check your connection and try again.");
      mood("worried", 5000);
    } finally {
      busy = false;
    }
  }

  chatForm.addEventListener("submit", (e) => { e.preventDefault(); send(msg.value.trim()); });

  pinForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (busy) return;
    busy = true;
    const value = pin.value;
    pin.value = "";
    resync();
    try {
      const data = await post("/api/confirm", { pin: value });
      reply(data.reply);
      applyState(data);
      if (!data.pending && !data.locked) msg.focus();
    } catch (e2) {
      reply("Sorry, I couldn't reach ClearCart. Nothing was charged.");
    } finally {
      busy = false;
    }
  });

  cancelBtn.addEventListener("click", async () => {
    const data = await post("/api/cancel");
    reply(data.reply);
    applyState(data);
    msg.focus();
  });

  unlockForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const value = unlockPin.value;
    unlockPin.value = "";
    resync();
    const data = await post("/api/unlock", { pin: value });
    reply(data.reply);
    applyState(data);
    if (data.ok) msg.focus();
  });

  // ---- Voice input (Chrome / Edge) ----
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const voiceStatus = document.getElementById("voice-status");
  function showVoice(s) { if (voiceStatus) voiceStatus.textContent = s; }

  function handleSpoken(text) {
    if (!confirmBox.hidden) {
      // While a payment or refund waits, voice never confirms it. Only the typed PIN does.
      if (/\b(cancel|stop|no)\b/i.test(text)) { cancelBtn.click(); return; }
      if (/\b(repeat|again)\b/i.test(text)) { say(readback.textContent); return; }
      reply("To confirm, type your 4-digit PIN in the box and press Enter. Or say cancel.");
      pin.focus();
      return;
    }
    send(text);
  }

  if (SR) {
    micBtn.hidden = false;
    const rec = new SR();
    rec.lang = "en-US";
    rec.continuous = true;        // keep listening while you talk (like Google's demo)
    rec.interimResults = true;    // show words as they are heard
    let listening = false, finalText = "", interimText = "", stopTimer = null;

    micBtn.addEventListener("click", () => {
      if (listening) { rec.stop(); return; }
      if (window.speechSynthesis) window.speechSynthesis.cancel();
      if (!speakBox.checked) { speakBox.checked = true; speakBox.dispatchEvent(new Event("change")); }
      finalText = ""; interimText = "";
      try { rec.start(); } catch (e) { showVoice("Could not start voice input: " + e.message); }
    });
    rec.onstart = () => {
      listening = true;
      mood("listening");
      micBtn.setAttribute("aria-pressed", "true");
      micBtn.textContent = "Listening… (press to stop)";
      showVoice("Listening…");
    };
    rec.onaudiostart = () => showVoice("Microphone on. Speak now.");
    rec.onspeechstart = () => showVoice("Hearing you…");
    rec.onresult = (e) => {
      interimText = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript;
        if (e.results[i].isFinal) finalText += t + " "; else interimText += t;
      }
      showVoice("Heard: " + (finalText + interimText).trim());
      clearTimeout(stopTimer);
      stopTimer = setTimeout(() => rec.stop(), 1500);   // stop after 1.5 seconds of silence
    };
    rec.onerror = (e) => {
      const msgs = {
        "not-allowed": "I can't use the microphone. Please allow microphone access, or type instead.",
        "service-not-allowed": "The browser's speech service is blocked. Please type instead.",
        "audio-capture": "I can't find a microphone. Check it's connected and allowed, or type instead.",
        "no-speech": "I didn't hear anything. Press Talk and speak after it says Listening.",
        "network": "Voice input needs the browser's online speech service, and it couldn't be reached. Please type instead.",
        "aborted": null
      };
      const text = (e.error in msgs) ? msgs[e.error] : "Voice input failed (" + e.error + "). Please type instead.";
      if (text) reply(text);
    };
    rec.onend = () => {
      listening = false;
      if (document.documentElement.dataset.mood === "listening") mood("idle");
      clearTimeout(stopTimer);
      micBtn.setAttribute("aria-pressed", "false");
      micBtn.textContent = "Talk";
      const text = (finalText + interimText).trim();
      showVoice("");
      if (text) handleSpoken(text);
    };
  } else {
    voiceNote.hidden = false;
  }

  const init = window.CLEARCART || {};
  if (init.locked || init.pending) applyState(init); else msg.focus();
})();
