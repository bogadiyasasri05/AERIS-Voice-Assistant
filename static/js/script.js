const micButton = document.getElementById("toggleMic");
const clearButton = document.getElementById("clearChat");
const transcriptBox = document.getElementById("transcript");
const responseBox = document.getElementById("response");
const stopAllButton = document.getElementById("stopAll");
const avatarContainer = document.querySelector('.avatar-container');

let recognition;
let isListening = false;

// Check for browser support
if (!("webkitSpeechRecognition" in window)) {
  alert("⚠️ Your browser does not support speech recognition. Try using Google Chrome.");
} else {
  recognition = new webkitSpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-US";

  recognition.onstart = () => {
    startSpeakingAnimation(); // mic started → start animation
  };

  recognition.onresult = (event) => {
    const spokenText = event.results[0][0].transcript;
    transcriptBox.textContent = `👤 You: ${spokenText}`;
    sendToBackend(spokenText);
  };

  recognition.onerror = (event) => {
    transcriptBox.textContent = `⚠️ Recognition error: ${event.error}`;
    stopSpeakingAnimation(); // stop animation on error
    console.error("Speech recognition error:", event.error);
  };

  recognition.onend = () => {
    stopSpeakingAnimation(); // mic stopped → stop animation
    if (isListening) recognition.start(); // auto-restart for continuous mode
  };
}

// Toggle microphone button
micButton.addEventListener("click", () => {
  console.log("Mic button clicked. isListening:", isListening);
  if (isListening) {
    recognition.stop();
    micButton.textContent = "🎤 Start Listening";
    isListening = false;
    stopSpeakingAnimation();
  } else {
    recognition.start();
    micButton.textContent = "🛑 Stop Listening";
    isListening = true;
    startSpeakingAnimation();
  }
});

// Clear chat boxes button
clearButton.addEventListener("click", () => {
  transcriptBox.textContent = "🎙️ Say something...";
  responseBox.textContent = "💬 I’ll respond here!";
});

// Send user input to Flask backend
function sendToBackend(text) {
  fetch("/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  })
    .then((res) => res.json())
    .then((data) => {
      responseBox.textContent = `🤖 Aeris: ${data.response}`;
      speak(data.response);
    })
    .catch((err) => {
      responseBox.textContent = "❌ Error contacting Aeris server.";
      console.error(err);
    });
}

// Speak Aeris response with speech synthesis
function speak(text) {
  if (!window.speechSynthesis) return;

  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = "en-US";

  utter.onstart = () => {
    startSpeakingAnimation(); // speaking started → start animation
  };

  utter.onend = () => {
    stopSpeakingAnimation(); // speaking ended → stop animation
  };

  utter.onerror = () => {
    stopSpeakingAnimation(); // error → stop animation
  };

  window.speechSynthesis.speak(utter);
}

// Stop everything button
stopAllButton.addEventListener('click', () => {
  // Stop microphone listening
  if (recognition && isListening) {
    try {
      recognition.abort(); // immediate stop
      console.log("Speech recognition stopped.");
    } catch (e) {
      console.warn("Recognition stop failed:", e);
    }
    micButton.textContent = "🎤 Start Listening";
    isListening = false;
  }

  // Stop text-to-speech speaking
  if (window.speechSynthesis && window.speechSynthesis.speaking) {
    window.speechSynthesis.cancel();
    console.log("Speech synthesis cancelled.");
  }

  // Stop avatar animation
  stopSpeakingAnimation();
});

// Avatar animation controls
function startSpeakingAnimation() {
  avatarContainer.classList.add('avatar-speaking');
}

function stopSpeakingAnimation() {
  avatarContainer.classList.remove('avatar-speaking');
}

// Feedback form submission
document.getElementById("feedbackForm").addEventListener("submit", function (e) {
  e.preventDefault();
  const formData = new FormData(this);

  fetch("/feedback", {
    method: "POST",
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      const msg = document.getElementById("formSuccessMsg");
      msg.textContent = data.success ? "✅ Message sent!" : "❌ Failed to send.";
      if (data.success) this.reset();
    })
    .catch(err => {
      document.getElementById("formSuccessMsg").textContent = "❌ Error occurred.";
      console.error("Error sending feedback:", err);
    });
});

// Update date and time display
function updateDateTime() {
  const now = new Date();
  document.getElementById("currentDateTime").textContent =
    now.toLocaleString('en-IN', { dateStyle: 'long', timeStyle: 'short' });
}
setInterval(updateDateTime, 1000);
updateDateTime();
