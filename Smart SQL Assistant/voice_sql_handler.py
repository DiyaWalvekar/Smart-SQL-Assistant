import whisper
import pyaudio
import numpy as np
import google.generativeai as genai
import re
from nlp_utils import match_intent, expand_query

# ---------- Configure Google AI API ----------
genai.configure(api_key="api_key")  # Replace with your actual key

# ---------- Load Whisper Model ----------
model_whisper = whisper.load_model("base")


# ---------- Audio Recording ----------
def record_audio(duration=5, rate=16000):
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=rate, input=True, frames_per_buffer=1024)
    frames = [np.frombuffer(stream.read(1024), dtype=np.int16) for _ in range(int(rate / 1024 * duration))]
    stream.stop_stream()
    stream.close()
    audio.terminate()
    return np.concatenate(frames).astype(np.float32) / 32768.0


def transcribe_audio():
    print("Listening... Please speak.")
    audio_data = record_audio()
    result = model_whisper.transcribe(audio_data, fp16=False)
    print("Transcribed text:", result['text'])
    return result['text']


# ---------- Gemini Text-to-SQL ----------
def text_to_sql(text):
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    prompt = f"""
    Convert this instruction into a valid SQL query:
    \"{text}\"
    Only output the SQL, nothing else.
    """
    response = model.generate_content(prompt)
    return response.text.strip()


# ---------- Insert Fix ----------
def handle_missing_columns(sql):
    insert_pattern = re.compile(r"INSERT INTO `?(\w+)`?\s?\(([^)]+)\)\s?VALUES\s?\(([^)]+)\);", re.IGNORECASE)

    match = insert_pattern.search(sql)
    if match:
        table = match.group(1)
        columns = match.group(2).split(',')
        values = match.group(3).split(',')

        columns = [col.strip() for col in columns]
        values = [val.strip() for val in values]
        values = ['NULL' if val == '' else val for val in values]

        return f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)});"

    return sql


# ---------- Main Logic ----------
def handle_text_or_voice_query(mode, text=None):
    if mode == "voice":
        text = transcribe_audio()

    # Step 1: Match intent and expand query
    intent, confidence = match_intent(text)
    expanded_text = expand_query(text)
    print(f"Detected intent: {intent}, Confidence: {confidence}")
    print(f"Expanded query: {expanded_text}")

    # Step 2: Convert expanded query to SQL using Gemini
    sql = text_to_sql(expanded_text)

    # Step 3: Fix missing values if needed
    sql = handle_missing_columns(sql)

    return sql


# ---------- Test Locally ----------
if __name__ == "__main__":
    mode_input = input("Choose mode (text/voice): ").strip().lower()
    if mode_input == "text":
        user_input = input("Enter your question: ")
        result_sql = handle_text_or_voice_query("text", user_input)
    elif mode_input == "voice":
        result_sql = handle_text_or_voice_query("voice")
    else:
        print("Invalid mode.")
        exit()

    print("\nGenerated SQL Query:\n", result_sql)
