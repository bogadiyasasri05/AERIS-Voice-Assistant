import os
import time
import json
import pygame
import webbrowser
import requests
import speech_recognition as sr
from gtts import gTTS
import google.generativeai as genai

# ---------------- Configuration ----------------
GEMINI_API_KEY = "AIzaSyDyqkfpK5boijYNffTsTJtAFpkhgS2ij2w"  # Replace with your actual Gemini API key
WEATHER_API_KEY = "ac8544aa18104e04bd2fe4bb008b1705"       # Replace with your actual OpenWeatherMap API key
LOG_FILE = "aeris_log.json"
SYSTEM_INSTRUCTION = (
    "You are Aeris, a helpful AI assistant created by your user. "
    "Speak clearly, stay concise, and always aim to be useful."
)

# ---------------- Gemini Setup ----------------
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")


# ---------------- Audio Setup ----------------
pygame.mixer.init()
recognizer = sr.Recognizer()
mic = sr.Microphone()

# ---------------- TTS ----------------
def speak(text):
    print(f"\n🤖 Aeris: {text}")
    if "```" in text:
        print("🚫 Skipping TTS for code block.")
        return
    tts = gTTS(text=text, lang='en', tld='com.au')
    audio_file = "response.mp3"
    tts.save(audio_file)
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    pygame.mixer.music.unload()
    os.remove(audio_file)

# ---------------- Logging ----------------
def log_interaction(user_input, response):
    log_data = {"user": user_input, "aeris": response}
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r+", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
            data.append(log_data)
            f.seek(0)
            json.dump(data, f, indent=2)
    else:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump([log_data], f, indent=2)

# ---------------- STT ----------------
def listen(prompt=None):
    try:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            if prompt:
                speak(prompt)
            print("🎧 Listening...")
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=20)
        command = recognizer.recognize_google(audio)
        print(f"👤 You: {command}")
        return command.lower()
    
    except sr.WaitTimeoutError:
        print("⚠️ Timeout: No speech detected.")
        speak("I didn't hear anything. Please try again.")
        
    except sr.UnknownValueError:
        print("⚠️ Recognition error: Unintelligible speech.")
        speak("Sorry, I didn't catch that.")
        
    except sr.RequestError:
        speak("Speech recognition service is down.")
        
    except Exception as e:
        print(f"⚠️ Other recognition error: {e}")
        speak("Something went wrong.")
        
    return None


# ---------------- Special Commands ----------------
def handle_special_commands(command):
    command = command.lower()
    if "open youtube" in command:
        webbrowser.open("https://youtube.com")
        speak("Opening YouTube.")
        return True
    elif "open google" in command:
        webbrowser.open("https://google.com")
        speak("Opening Google.")
        return True
    elif "open chrome" in command:
        try:
            os.startfile("chrome")
            speak("Opening Chrome.")
        except Exception:
            speak("I couldn't find Chrome.")
        return True
    elif "open notepad" in command:
        os.system("notepad")
        speak("Opening Notepad.")
        return True
    elif "weather" in command:
        return handle_weather(command)
    elif "open downloads" in command:
        path = os.path.join(os.path.expanduser("~"), "Downloads")
        os.startfile(path)
        speak("Opening Downloads folder.")
        return True
    elif "open resume" in command:
        file_path = os.path.expanduser("~/Documents/SST_Resume.docx")
        try:
            os.startfile(file_path)
            speak("Opening your resume.")
        except Exception:
            speak("I couldn't open the resume file.")
        return True
    return False

# ---------------- Weather ----------------
def handle_weather(command):
    speak("Which city?")
    city = listen()
    if not city:
        return True
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        res = requests.get(url).json()
        if res.get("cod") != 200:
            speak("I couldn't find that city.")
            return True
        temp = res["main"]["temp"]
        desc = res["weather"][0]["description"]
        response = f"The weather in {city.title()} is {desc} with {temp} degrees Celsius."
        speak(response)
        log_interaction(f"weather in {city}", response)
    except Exception as e:
        print(f"Error getting weather: {e}")
        speak("I had trouble getting the weather.")
    return True

# ---------------- Aeris AI Response ----------------
def get_aeris_response(user_text, retries=2):
    try:
        full_prompt = f"{SYSTEM_INSTRUCTION}\nUser: {user_text}\nAeris:"
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        if retries > 0:
            time.sleep(1)
            return get_aeris_response(user_text, retries - 1)
        return "Sorry, I'm having trouble right now."

# ---------------- Main Loop ----------------
def run_aeris():
    speak("Hello! I'm Aeris, your assistant. Ask me anything.")
    while True:
        command = listen()
        if not command:
            continue
        if any(kw in command for kw in ["exit", "goodbye", "shut down", "quit"]):
            speak("Goodbye! Have a great day.")
            break
        if handle_special_commands(command):
            continue
        try:
            print("🧠 Thinking...")
            full_text = get_aeris_response(command)
            print(full_text)
            speak(full_text)
            log_interaction(command, full_text)
        except Exception as e:
            print("❌ Gemini error:", e)
            speak("I'm having trouble connecting to my brain right now.")

# ---------------- Start Assistant ----------------
if __name__ == "__main__":
    try:
        run_aeris()
    except KeyboardInterrupt:
        print("\n👋 Aeris has been shut down.")
        speak("Goodbye!")
