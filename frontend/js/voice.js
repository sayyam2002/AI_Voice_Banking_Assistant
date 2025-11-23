// voice.js — final version
// Usage: include this on pages that have #start-voice-btn and #voice-result elements.

let mediaRecorder = null;
let audioChunks = [];

// --- Record helpers ---
async function initMedia() {
  return await navigator.mediaDevices.getUserMedia({ audio: true });
}

// Convert WebM/AudioBuffer -> WAV (16-bit PCM)
async function convertWebmToWav(webmBlob) {
  const arrayBuffer = await webmBlob.arrayBuffer();
  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);

  // If stereo, convert to mono by averaging channels
  const numChannels = audioBuffer.numberOfChannels;
  const sampleRate = audioBuffer.sampleRate;
  const length = audioBuffer.length;
  const mono = new Float32Array(length);
  for (let c = 0; c < numChannels; c++) {
    const chData = audioBuffer.getChannelData(c);
    for (let i = 0; i < length; i++) mono[i] += chData[i] / numChannels;
  }

  // resample to 16000 if needed
  let targetRate = 16000;
  let finalFloat32 = mono;
  if (sampleRate !== targetRate) {
    // simple offline resampling using OfflineAudioContext for reliability
    const offlineCtx = new (window.OfflineAudioContext ||
      window.webkitOfflineAudioContext)(
      1,
      Math.ceil((length * targetRate) / sampleRate),
      targetRate
    );
    const buffer = offlineCtx.createBuffer(1, length, sampleRate);
    buffer.copyToChannel(mono, 0, 0);
    const source = offlineCtx.createBufferSource();
    source.buffer = buffer;
    source.connect(offlineCtx.destination);
    source.start(0);
    const rendered = await offlineCtx.startRendering();
    finalFloat32 = rendered.getChannelData(0);
  }

  // Build WAV (16-bit PCM)
  const bytesPerSample = 2;
  const blockAlign = bytesPerSample * 1;
  const wavBuffer = new ArrayBuffer(44 + finalFloat32.length * bytesPerSample);
  const view = new DataView(wavBuffer);

  function writeString(view, offset, str) {
    for (let i = 0; i < str.length; i++) {
      view.setUint8(offset + i, str.charCodeAt(i));
    }
  }

  let offset = 0;
  writeString(view, offset, "RIFF");
  offset += 4;
  view.setUint32(offset, 36 + finalFloat32.length * bytesPerSample, true);
  offset += 4;
  writeString(view, offset, "WAVE");
  offset += 4;
  writeString(view, offset, "fmt ");
  offset += 4;
  view.setUint32(offset, 16, true);
  offset += 4; // subchunk1 size
  view.setUint16(offset, 1, true);
  offset += 2; // PCM
  view.setUint16(offset, 1, true);
  offset += 2; // channels
  view.setUint32(offset, targetRate, true);
  offset += 4;
  view.setUint32(offset, targetRate * blockAlign, true);
  offset += 4;
  view.setUint16(offset, blockAlign, true);
  offset += 2;
  view.setUint16(offset, 16, true);
  offset += 2; // bits per sample
  writeString(view, offset, "data");
  offset += 4;
  view.setUint32(offset, finalFloat32.length * bytesPerSample, true);
  offset += 4;

  // PCM16 little endian
  let pos = 44;
  for (let i = 0; i < finalFloat32.length; i++, pos += 2) {
    let s = Math.max(-1, Math.min(1, finalFloat32[i]));
    view.setInt16(pos, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }

  return new Blob([view], { type: "audio/wav" });
}

// Record for `seconds` and return WAV Blob
async function recordAndGetWav(seconds = 3) {
  const stream = await initMedia();
  mediaRecorder = new MediaRecorder(stream);

  audioChunks = [];
  mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);

  return new Promise((resolve) => {
    mediaRecorder.onstop = async () => {
      const webmBlob = new Blob(audioChunks, {
        type: audioChunks[0]?.type || "audio/webm",
      });

      // simple file size sanity check
      if (webmBlob.size < 3000) {
        resolve(null);
        return;
      }

      try {
        const wavBlob = await convertWebmToWav(webmBlob);
        resolve(wavBlob);
      } catch (e) {
        console.error("WAV conversion error:", e);
        resolve(null);
      }
    };

    mediaRecorder.start();
    setTimeout(() => {
      try {
        mediaRecorder.stop();
      } catch (e) {
        console.warn(e);
      }
    }, seconds * 1000);
  });
}

// Send WAV Blob (expects 16k mono PCM) to backend /voice/asr
async function sendAudioToBackend(wavBlob) {
  const voiceResultDiv = document.getElementById("voice-result");
  if (!wavBlob) {
    voiceResultDiv.innerHTML = "❌ Invalid or empty audio";
    return;
  }

  // debug: allow download of recorded wav
  try {
    const url = URL.createObjectURL(wavBlob);
    console.debug("Recorded WAV blob URL:", url);
    // optional: create a quick download link for debugging
    // let a = document.createElement("a"); a.href = url; a.download = "debug.wav"; a.textContent = "Download debug.wav"; document.body.appendChild(a);
  } catch (e) {
    /* ignore */
  }

  const form = new FormData();
  form.append("file", wavBlob, "input.wav");

  const token = localStorage.getItem("token");

  try {
    const res = await fetch("http://127.0.0.1:8000/voice/asr", {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    });

    const data = await res.json();

    if (data.error) {
      document.getElementById("voice-result").innerHTML =
        "❌ ASR Error: " + data.error;
      console.error("ASR error:", data.error);
      return;
    }

    if (!data.text) {
      document.getElementById("voice-result").innerHTML = "❌ No text returned";
      return;
    }

    // document.getElementById("voice-result").innerHTML = "🗣 " + data.text;
    const nluRes = await fetch("http://127.0.0.1:8000/nlu/detect-intent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: data.text }),
    });

    const nluData = await nluRes.json();
    console.log("NLU:", nluData);

    if (nluData.intent === "check_balance") {
      const token = localStorage.getItem("token");
      const balRes = await fetch("http://127.0.0.1:8000/accounts/balance", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const balData = await balRes.json();

      console.log("BALANCE RESPONSE:", balData);

      if (!Array.isArray(balData) || balData.length === 0) {
        voiceResultDiv.innerHTML = "💰 You have no accounts.";
        return;
      }

      let html = `
    <div style="
      font-size: 20px;
      font-weight: 700;
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      gap: 8px;
    ">
      💰 Your Accounts
    </div>

    <div style="
      display: flex !important;
      flex-direction: row !important;
      flex-wrap: nowrap !important;
      gap: 25px !important;
      overflow-x: auto !important;
      padding-bottom: 10px;
      width: 100%;
      scrollbar-width: thin;
    ">
  `;

      for (const acc of balData) {
        html += `
      <div style="
        min-width: 220px;
        background: white;
        border-radius: 12px;
        padding: 18px;
        text-align: left;
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
        border: 1px solid #eee;
        flex-shrink: 0;
      ">
        <div style="font-weight: 700; font-size: 18px; margin-bottom: 10px;">
          ${acc.account_type}
        </div>

        <div style="line-height: 1.7; font-size: 15px;">
          <strong>Balance:</strong> ₹${acc.balance}<br>
          <strong>Account ID:</strong> ${acc.id}
        </div>
      </div>
    `;
      }

      html += `</div>`;

      voiceResultDiv.innerHTML = html;
    } else if (nluData.intent === "get_history") {
      const token = localStorage.getItem("token");
      const trRes = await fetch("http://127.0.0.1:8000/transactions/", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const transactions = await trRes.json();

      console.log("TRANSACTIONS:", transactions);

      if (!Array.isArray(transactions) || transactions.length === 0) {
        voiceResultDiv.innerHTML = "📄 No recent transactions found.";
        return;
      }

      let html = `
    <div style="
      font-size: 20px;
      font-weight: 700;
      margin-bottom: 15px;
    ">
      📄 Recent Transactions
    </div>

    <ul style="
      list-style: none;
      padding: 0;
      margin: 0;
      display: flex;
      flex-direction: column;
      gap: 14px;
    ">
  `;

      for (const t of transactions.slice(0, 6)) {
        html += `
      <li style="
        background: white;
        padding: 14px 18px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.07);
        border: 1px solid #eee;
        font-size: 15px;
        line-height: 1.6;
      ">
        <strong>${t.type.toUpperCase()}</strong> — ₹${t.amount}<br>
        ${t.description}<br>
        <span style="font-size: 13px; color: #666;">${t.date}</span>
      </li>
    `;
      }

      html += `</ul>`;

      voiceResultDiv.innerHTML = html;
    } else if (nluData.intent === "ask_loan") {
      const loanRes = await fetch("http://127.0.0.1:8000/loans/info");
      const loans = await loanRes.json();

      console.log("LOANS:", loans);

      if (!Array.isArray(loans) || loans.length === 0) {
        voiceResultDiv.innerHTML = "💸 No loan products found.";
        return;
      }

      let html = `
    <div style="
      font-size: 20px;
      font-weight: 700;
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      gap: 8px;
    ">
      💸 Available Loan Options
    </div>

    <!-- HARD-LOCKED HORIZONTAL CONTAINER -->
    <div style="
      display: flex !important;
      flex-direction: row !important;
      flex-wrap: nowrap !important;
      gap: 25px !important;
      overflow-x: auto !important;
      padding: 10px;
      scrollbar-width: thin;
      width: 100%;
    ">
  `;

      for (const loan of loans) {
        html += `
      <div style="
        min-width: 240px;
        background: white;
        border-radius: 14px;
        padding: 18px;
        text-align: left;
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
        border: 1px solid #eee;
        flex-shrink: 0;
      ">
        <div style="font-weight: 700; font-size: 18px; text-transform: capitalize; margin-bottom: 10px;">
          ${loan.loan_type}
        </div>

        <div style="line-height: 1.7; font-size: 15px;">
          <strong>Interest:</strong> ${loan.interest_rate}%<br>
          <strong>Amount:</strong> ₹${loan.min_amount} - ₹${loan.max_amount}<br>
          <strong>Tenure:</strong> ${loan.tenure} months
        </div>
      </div>
    `;
      }

      html += `</div>`;

      voiceResultDiv.innerHTML = html;
    } else {
      voiceResultDiv.innerHTML = `🗣 ${data.text}<br> Sorry, I cannot understand your voice`;   //Intent: ${nluData.intent}
    }
  } catch (err) {
    console.error("sendAudioToBackend failed:", err);
    document.getElementById("voice-result").innerHTML =
      "❌ Network / fetch error";
  }
}

// UI wiring (dashboard)
const voiceBtn = document.getElementById("start-voice-btn");
const voiceResultDiv = document.getElementById("voice-result");

if (voiceBtn) {
  voiceBtn.addEventListener("click", async () => {
    voiceResultDiv.innerHTML = "Listening... 🎤";
    const wavBlob = await recordAndGetWav(3);
    if (!wavBlob) {
      voiceResultDiv.innerHTML = "❌ Failed to capture/convert audio";
      return;
    }
    voiceResultDiv.innerHTML = "Processing...";
    await sendAudioToBackend(wavBlob);
  });
}
