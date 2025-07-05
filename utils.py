import os
import json
import requests
from gtts import gTTS
import pygame
import google.generativeai as genai

# ----------- Configuration -----------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "YOUR_GEMINI_API_KEY"
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY") or "YOUR_OPENWEATHER_API_KEY"
LOG_FILE = "logs/aeris_log.json"
SYSTEM_INSTRUCTION = "You are Aeris, a helpful AI assistant. Be concise, clear, and friendly."

# ----------- Setup -----------
pygame.mixer.init()
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(
    model_name="models/gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)
chat = model.start_chat(history=[])


# ----------- Logging -----------
def log_interaction(user_input, aeris_response):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    log_entry = {"user": user_input, "aeris": aeris_response}
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r+", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
            data.append(log_entry)
            f.seek(0)
            json.dump(data, f, indent=2)
    else:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump([log_entry], f, indent=2)


# ----------- TTS Playback -----------
def speak(text):
    if "```" in text:
        print("🛑 Skipping TTS for code block.")
        return
    tts = gTTS(text=text, lang='en', tld='com.au')
    tts.save("response.mp3")
    pygame.mixer.music.load("response.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pass
    pygame.mixer.music.unload()
    os.remove("response.mp3")


# ----------- Gemini Query -----------
def get_gemini_response(prompt):
    try:
        print("🔮 Sending to Gemini...")
        response = chat.send_message(prompt)
        log_interaction(prompt, response.text)
        return response.text
    except Exception as e:
        print("❌ Gemini Error:", e)
        return "Sorry, I'm having trouble accessing my brain right now."


# ----------- Weather Info -----------
def get_weather(city_name):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={WEATHER_API_KEY}&units=metric"
        res = requests.get(url).json()
        if res.get("cod") != 200:
            return f"I couldn't find the weather for {city_name}."
        temp = res["main"]["temp"]
        desc = res["weather"][0]["description"]
        response = f"The weather in {city_name.title()} is {desc} with {temp} degrees Celsius."
        log_interaction(f"weather in {city_name}", response)
        return response
    except Exception as e:
        print("❌ Weather Error:", e)
        return "I had trouble getting the weather data."
