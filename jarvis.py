"""
╔══════════════════════════════════════════════════════════════╗
║                    J.A.R.V.I.S                               ║
║          Just A Rather Very Intelligent System               ║
║                                                              ║
║   Voice Assistant for macOS - Python 3.14 Compatible         ║
║   Works in PyCharm - No PyAudio Required                     ║
╚══════════════════════════════════════════════════════════════╝

SETUP INSTRUCTIONS:
    1. Install portaudio (in macOS Terminal):
         brew install portaudio

    2. Install packages (in PyCharm Terminal):
         pip install sounddevice numpy SpeechRecognition pyttsx3 requests pyobjc python-dotenv

    3. Get a FREE News API key from:
         https://newsapi.org/register

    4. Create a .env file in the project folder and add:
         NEWS_API_KEY=your_key_here

    5. Grant microphone permission:
         System Settings → Privacy & Security → Microphone → Enable PyCharm
         Then RESTART PyCharm completely (Cmd+Q, reopen)

    6. Click the green Run ▶ button!
"""

import os
import wave
import datetime
import webbrowser
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Third-party imports
try:
    import sounddevice as sd
except ImportError:
    print("ERROR: sounddevice not installed!")
    print("Run: pip install sounddevice")
    print("Also make sure portaudio is installed: brew install portaudio")
    exit(1)

try:
    import speech_recognition as sr
except ImportError:
    print("ERROR: SpeechRecognition not installed!")
    print("Run: pip install SpeechRecognition")
    exit(1)

try:
    import pyttsx3
except ImportError:
    print("ERROR: pyttsx3 not installed!")
    print("Run: pip install pyttsx3 pyobjc")
    exit(1)

try:
    import requests
except ImportError:
    print("ERROR: requests not installed!")
    print("Run: pip install requests")
    exit(1)


# ╔══════════════════════════════════════════════════════════════╗
# ║                     CONFIGURATION                           ║
# ╚══════════════════════════════════════════════════════════════╝

NEWS_API_KEY = os.getenv("NEWS_API_KEY")  # Loaded from .env file
USER_NAME = "Sir"
DEFAULT_CITY = "Raipur"
RECORD_DURATION = 5       # Seconds to listen (increase to 7 if it cuts you off)
SAMPLE_RATE = 16000        # Audio sample rate (don't change)
TEMP_AUDIO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_audio.wav")


# ╔══════════════════════════════════════════════════════════════╗
# ║                  TEXT-TO-SPEECH ENGINE                       ║
# ╚══════════════════════════════════════════════════════════════╝

def init_engine():
    """Initialize and return the TTS engine with error handling."""
    try:
        eng = pyttsx3.init()
        voices = eng.getProperty('voices')
        if voices:
            eng.setProperty('voice', voices[0].id)
        eng.setProperty('rate', 175)
        eng.setProperty('volume', 1.0)
        return eng
    except Exception as e:
        print(f"WARNING: Text-to-speech init failed: {e}")
        print("JARVIS will print responses instead of speaking.")
        return None


engine = init_engine()


def speak(text):
    """Convert text to speech and print to console."""
    print(f"\n  JARVIS: {text}")
    if engine:
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception:
            pass  # If speech fails, text is already printed


# ╔══════════════════════════════════════════════════════════════╗
# ║                   VOICE INPUT (MICROPHONE)                  ║
# ╚══════════════════════════════════════════════════════════════╝

def check_microphone():
    """Check if a microphone is available and accessible."""
    try:
        devices = sd.query_devices()
        default_input = sd.default.device[0]
        if default_input < 0:
            print("WARNING: No default input device found!")
            print("Available devices:")
            print(devices)
            return False
        input_device = sd.query_devices(default_input)
        print(f"  Microphone: {input_device['name']}")
        return True
    except Exception as e:
        print(f"  Microphone check failed: {e}")
        return False


def take_command():
    """
    Record audio from microphone, save to WAV file, and recognize speech.
    Uses sounddevice (no PyAudio needed) - Python 3.14 compatible.
    Returns recognized text in lowercase, or empty string on failure.
    """
    recognizer = sr.Recognizer()

    # Step 1: Record audio
    print(f"\n  🎤 Listening for {RECORD_DURATION} seconds... (speak now)")
    try:
        recording = sd.rec(
            int(RECORD_DURATION * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype='int16'
        )
        sd.wait()  # Block until recording is finished
    except Exception as e:
        print(f"  Microphone error: {e}")
        print("  TIP: Check System Settings → Privacy & Security → Microphone → PyCharm")
        return ""

    # Step 2: Check if audio was actually captured
    if recording is None or len(recording) == 0:
        speak("No audio was captured. Please check your microphone.")
        return ""

    max_amplitude = int(abs(recording).max())
    print(f"  Audio level: {max_amplitude}", end="")

    if max_amplitude < 50:
        print(" (too quiet - didn't hear anything)")
        speak("I didn't hear anything. Please speak louder.")
        return ""
    else:
        print(" (audio captured)")

    # Step 3: Save recording to a WAV file on disk
    try:
        with wave.open(TEMP_AUDIO_FILE, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit audio = 2 bytes
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(recording.tobytes())
    except Exception as e:
        print(f"  Error saving audio file: {e}")
        return ""

    # Step 4: Recognize speech from the WAV file
    try:
        with sr.AudioFile(TEMP_AUDIO_FILE) as source:
            audio = recognizer.record(source)

        print("  Recognizing...")
        query = recognizer.recognize_google(audio, language='en-in')
        print(f"  ✅ You said: {query}")
        return query.lower()

    except sr.UnknownValueError:
        print("  Could not understand audio")
        speak("Sorry, I didn't catch that. Please repeat.")
        return ""
    except sr.RequestError as e:
        print(f"  Google API error: {e}")
        speak("Network error. Please check your internet connection.")
        return ""
    except Exception as e:
        print(f"  Recognition error: {e}")
        return ""
    finally:
        # Clean up temp file
        try:
            if os.path.exists(TEMP_AUDIO_FILE):
                os.remove(TEMP_AUDIO_FILE)
        except OSError:
            pass


# ╔══════════════════════════════════════════════════════════════╗
# ║                     NEWS FUNCTIONS                          ║
# ╚══════════════════════════════════════════════════════════════╝

def get_news(category=None, country="us"):
    """Fetch top headlines from NewsAPI by category."""
    if not NEWS_API_KEY:
        speak("You need to set your News API key first. "
              "Get a free key from newsapi.org and add it to the .env file.")
        return

    url = f"https://newsapi.org/v2/top-headlines?country={country}&apiKey={NEWS_API_KEY}"
    if category:
        url += f"&category={category}"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("status") != "ok":
            speak("The news service returned an error. Please check your API key.")
            print(f"  API response: {data.get('message', 'Unknown error')}")
            return

        articles = data.get("articles", [])
        if not articles:
            speak("I couldn't find any news at the moment.")
            return

        count = min(5, len(articles))
        category_text = f" {category}" if category else ""
        speak(f"Here are the top {count}{category_text} headlines.")

        for i, article in enumerate(articles[:5], 1):
            title = article.get("title", "No title available")
            source = article.get("source", {}).get("name", "Unknown")
            speak(f"Headline {i}: {title}")
            print(f"    Source: {source}")

    except requests.exceptions.Timeout:
        speak("The news request timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        speak("Could not connect to the news service. Check your internet.")
    except Exception as e:
        speak("I couldn't fetch the news right now.")
        print(f"  Error: {e}")


def get_world_news():
    """Fetch international news from around the globe."""
    if not NEWS_API_KEY:
        speak("You need to set your News API key first. "
              "Get a free key from newsapi.org and add it to the .env file.")
        return

    url = (f"https://newsapi.org/v2/everything?"
           f"q=world+OR+international&sortBy=publishedAt"
           f"&language=en&pageSize=5&apiKey={NEWS_API_KEY}")
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        articles = data.get("articles", [])[:5]

        if not articles:
            speak("No world news available right now.")
            return

        speak("Here's what's happening around the world.")
        for i, article in enumerate(articles, 1):
            title = article.get("title", "")
            source = article.get("source", {}).get("name", "Unknown")
            speak(f"{i}. {title}")
            print(f"    Source: {source}")

    except Exception as e:
        speak("Unable to fetch world news.")
        print(f"  Error: {e}")


def get_india_news():
    """Fetch top news from India."""
    get_news(country="in")


# ╔══════════════════════════════════════════════════════════════╗
# ║                    WEATHER FUNCTION                         ║
# ╚══════════════════════════════════════════════════════════════╝

def get_weather(city=None):
    """Fetch current weather using free wttr.in service (no API key needed)."""
    if not city:
        city = DEFAULT_CITY

    try:
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=10)
        data = response.json()

        current = data["current_condition"][0]
        temp_c = current["temp_C"]
        desc = current["weatherDesc"][0]["value"]
        humidity = current["humidity"]
        feels_like = current["FeelsLikeC"]
        wind_speed = current["windspeedKmph"]

        report = (
            f"The weather in {city} is currently {desc}. "
            f"Temperature is {temp_c} degrees Celsius, "
            f"feels like {feels_like} degrees. "
            f"Humidity is {humidity} percent "
            f"and wind speed is {wind_speed} kilometers per hour."
        )
        speak(report)

    except requests.exceptions.ConnectionError:
        speak(f"Could not connect to weather service. Check your internet.")
    except KeyError:
        speak(f"I couldn't find weather data for {city}. Try a different city name.")
    except Exception as e:
        speak(f"I couldn't get the weather for {city}.")
        print(f"  Error: {e}")


# ╔══════════════════════════════════════════════════════════════╗
# ║                   UTILITY FUNCTIONS                         ║
# ╚══════════════════════════════════════════════════════════════╝

def tell_time():
    """Announce the current time."""
    now = datetime.datetime.now().strftime("%I:%M %p")
    speak(f"The time is {now}")


def tell_date():
    """Announce today's full date."""
    today = datetime.datetime.now().strftime("%A, %B %d, %Y")
    speak(f"Today is {today}")


def open_website(url, name):
    """Open a website in the default browser."""
    speak(f"Opening {name}")
    webbrowser.open(url)


def google_search(term):
    """Search Google for a term."""
    speak(f"Searching Google for {term}")
    webbrowser.open(f"https://www.google.com/search?q={term}")


def youtube_search(term):
    """Search YouTube for a term."""
    speak(f"Searching YouTube for {term}")
    webbrowser.open(f"https://www.youtube.com/results?search_query={term}")


def tell_joke():
    """Tell a random joke using a free API."""
    try:
        response = requests.get(
            "https://official-joke-api.appspot.com/random_joke",
            timeout=5
        )
        joke = response.json()
        speak(joke["setup"])
        import time
        time.sleep(1.5)
        speak(joke["punchline"])
    except Exception:
        speak("Why do programmers prefer dark mode? "
              "Because light attracts bugs!")


def system_info():
    """Report basic system information."""
    import platform
    system = platform.system()
    machine = platform.machine()
    python_ver = platform.python_version()
    speak(f"You are running {system} on {machine} with Python {python_ver}.")


# ╔══════════════════════════════════════════════════════════════╗
# ║                   HELP / COMMANDS LIST                      ║
# ╚══════════════════════════════════════════════════════════════╝

def show_help():
    """Display available commands."""
    speak("Here's what I can do.")
    commands = """
    ╔═══════════════════════════════════════════════════════╗
    ║              JARVIS - AVAILABLE COMMANDS              ║
    ╠═══════════════════════════════════════════════════════╣
    ║                                                       ║
    ║  NEWS:                                                ║
    ║    "news" / "headlines"    → Top headlines             ║
    ║    "world news"            → International news        ║
    ║    "India news"            → News from India           ║
    ║    "technology news"       → Tech headlines            ║
    ║    "sports news"           → Sports headlines          ║
    ║    "business news"         → Business headlines        ║
    ║    "health news"           → Health headlines          ║
    ║    "science news"          → Science headlines         ║
    ║    "entertainment news"    → Entertainment headlines   ║
    ║                                                       ║
    ║  WEATHER:                                             ║
    ║    "weather"               → Weather in your city      ║
    ║    "weather in London"     → Weather in any city       ║
    ║                                                       ║
    ║  TIME & DATE:                                         ║
    ║    "what time is it"       → Current time              ║
    ║    "what's the date"       → Today's date              ║
    ║                                                       ║
    ║  WEB:                                                 ║
    ║    "open YouTube"          → Opens YouTube             ║
    ║    "open Google"           → Opens Google              ║
    ║    "open GitHub"           → Opens GitHub              ║
    ║    "search for X"          → Google search             ║
    ║    "play X on YouTube"     → YouTube search            ║
    ║                                                       ║
    ║  FUN:                                                 ║
    ║    "tell me a joke"        → Random joke               ║
    ║    "system info"           → System information        ║
    ║                                                       ║
    ║  GENERAL:                                             ║
    ║    "help"                  → Show this list            ║
    ║    "goodbye" / "exit"      → Shut down JARVIS          ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """
    print(commands)


# ╔══════════════════════════════════════════════════════════════╗
# ║                    COMMAND PROCESSOR                        ║
# ╚══════════════════════════════════════════════════════════════╝

def extract_city_from_query(query):
    """Extract city name after 'in' from a weather query."""
    words = query.split()
    if "in" in words:
        idx = words.index("in")
        city = " ".join(words[idx + 1:]).strip("?.,!")
        return city if city else None
    return None


def process_command(query):
    """
    Route voice commands to the appropriate function.
    Returns False if the user wants to exit, True otherwise.
    """
    if not query:
        return True

    # ---- EXIT ----
    if any(word in query for word in ["exit", "quit", "stop", "goodbye",
                                       "bye", "shut down", "shutdown",
                                       "turn off", "sleep"]):
        speak(f"Goodbye {USER_NAME}. It was a pleasure assisting you. Have a wonderful day.")
        return False

    # ---- HELP ----
    elif "help" in query or "what can you do" in query:
        show_help()

    # ---- WORLD / INTERNATIONAL NEWS ----
    elif any(phrase in query for phrase in ["world news", "international news",
                                             "global news", "around the world",
                                             "current situation"]):
        get_world_news()

    # ---- INDIA NEWS ----
    elif "india" in query and "news" in query:
        get_india_news()

    # ---- CATEGORY NEWS ----
    elif "news" in query or "headlines" in query:
        if "sport" in query:
            get_news(category="sports")
        elif "tech" in query or "technology" in query:
            get_news(category="technology")
        elif "business" in query or "finance" in query or "market" in query:
            get_news(category="business")
        elif "health" in query or "medical" in query:
            get_news(category="health")
        elif "science" in query:
            get_news(category="science")
        elif "entertainment" in query or "movie" in query or "bollywood" in query:
            get_news(category="entertainment")
        else:
            get_news()

    # ---- WEATHER ----
    elif "weather" in query or "temperature" in query:
        city = extract_city_from_query(query)
        get_weather(city)

    # ---- TIME ----
    elif "time" in query and ("what" in query or "tell" in query or "current" in query):
        tell_time()

    # ---- DATE ----
    elif "date" in query or "today" in query or "day is it" in query:
        tell_date()

    # ---- YOUTUBE ----
    elif "open youtube" in query:
        open_website("https://youtube.com", "YouTube")
    elif "play" in query and "youtube" in query:
        term = query.replace("play", "").replace("on youtube", "").replace("youtube", "").strip()
        if term:
            youtube_search(term)
        else:
            open_website("https://youtube.com", "YouTube")

    # ---- GOOGLE ----
    elif "open google" in query:
        open_website("https://google.com", "Google")

    # ---- GITHUB ----
    elif "open github" in query:
        open_website("https://github.com", "GitHub")

    # ---- GOOGLE SEARCH ----
    elif "search" in query or "google" in query:
        term = (query.replace("search", "")
                .replace("for", "")
                .replace("google", "")
                .strip())
        if term:
            google_search(term)
        else:
            speak("What would you like me to search for?")

    # ---- OPEN WEBSITES ----
    elif "open" in query:
        site = query.replace("open", "").strip()
        if site:
            url = site if site.startswith("http") else f"https://www.{site}.com"
            open_website(url, site)

    # ---- JOKES ----
    elif "joke" in query:
        tell_joke()

    # ---- SYSTEM INFO ----
    elif "system" in query and "info" in query:
        system_info()

    # ---- IDENTITY ----
    elif "who are you" in query or "your name" in query:
        speak("I am JARVIS, Just A Rather Very Intelligent System. "
              "Your personal voice assistant.")
    elif "who made you" in query or "who created you" in query:
        speak("I was built using Python, running right here on your MacBook.")
    elif "how are you" in query:
        speak("I am functioning at optimal capacity. Thank you for asking.")

    # ---- GREETINGS ----
    elif any(word in query for word in ["hello", "hi", "hey"]):
        speak(f"Hello {USER_NAME}! How can I help you?")
    elif "thank you" in query or "thanks" in query:
        speak("You're welcome! Always happy to help.")

    # ---- UNKNOWN COMMAND ----
    else:
        speak(f"I'm not sure how to help with that. Say 'help' to see what I can do.")

    return True


# ╔══════════════════════════════════════════════════════════════╗
# ║                       GREETING                              ║
# ╚══════════════════════════════════════════════════════════════╝

def wish_user():
    """Greet the user based on current time of day."""
    hour = datetime.datetime.now().hour
    if 0 <= hour < 12:
        speak(f"Good morning {USER_NAME}")
    elif 12 <= hour < 18:
        speak(f"Good afternoon {USER_NAME}")
    else:
        speak(f"Good evening {USER_NAME}")
    speak("I am JARVIS, your personal assistant. How may I help you today?")


# ╔══════════════════════════════════════════════════════════════╗
# ║                        MAIN LOOP                            ║
# ╚══════════════════════════════════════════════════════════════╝

def main():
    """Main entry point - startup checks and command loop."""
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║               J.A.R.V.I.S  Starting Up...                   ║")
    print("║         Just A Rather Very Intelligent System                ║")
    print("║                                                              ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  Checking systems...                                         ║")

    # System checks
    print("║                                                              ║")
    print(f"║  Python: {__import__('platform').python_version():50s}║")
    mic_ok = check_microphone()
    tts_ok = "Ready" if engine else "Failed (text-only mode)"
    print(f"║  Speech Engine: {tts_ok:43s}║")
    api_ok = "Configured" if NEWS_API_KEY else "NOT SET (create a .env file with NEWS_API_KEY)"
    print(f"║  News API: {api_ok:48s}║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    if not mic_ok:
        print("⚠️  Microphone not detected!")
        print("   1. Check System Settings → Privacy & Security → Microphone")
        print("   2. Make sure PyCharm has microphone permission")
        print("   3. Restart PyCharm completely (Cmd+Q, then reopen)")
        print()
        choice = input("Continue without microphone? (y/n): ").strip().lower()
        if choice != 'y':
            print("Exiting. Fix microphone and try again.")
            return

    # Start JARVIS
    wish_user()

    print("\n  💡 TIP: Say 'help' to see all available commands")
    print("  💡 TIP: Say 'goodbye' or 'exit' to shut down JARVIS\n")

    running = True
    while running:
        try:
            query = take_command()
            running = process_command(query)
        except KeyboardInterrupt:
            speak(f"\nGoodbye {USER_NAME}. Shutting down.")
            running = False
        except Exception as e:
            print(f"\n  Unexpected error: {e}")
            print("  Recovering... ready for next command.")
            continue

    print("\n  JARVIS has shut down. See you next time! 👋\n")


if __name__ == "__main__":
    main()