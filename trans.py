import sounddevice as sd
import numpy as np
import speech_recognition as sr
from deep_translator import GoogleTranslator
import tkinter as tk
from threading import Thread
import queue
import time
import pyaudio

# 전역 변수
translator = None
running = False
root = None
subtitle_label = None
recognizer = sr.Recognizer()
audio_queue = queue.Queue()

# 지원하는 언어 목록
LANGUAGES = {
    "영어": "en",
    "일본어": "ja",
    "중국어": "zh-CN",
    "러시아어": "ru",
    "한국어": "ko"
}

input_lang = "en"
output_lang = "ko"

def get_audio_devices():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    devices = []
    for i in range(numdevices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        if device_info.get('maxInputChannels') > 0:
            devices.append({
                'name': device_info.get('name'),
                'index': i
            })
    p.terminate()
    return devices


def audio_callback(in_data, frame_count, time_info, status):
    global running
    if running:
        audio_queue.put(in_data)
    return (in_data, pyaudio.paContinue)

def process_audio():
    global running, translator
    print("Audio processing started")
    buffer = []
    silent_chunks = 0
    is_speaking = False

    while running:
        if not audio_queue.empty():
            chunk = audio_queue.get()
            buffer.append(chunk)
            
            # 음성 활성화 감지
            chunk_np = np.frombuffer(chunk, dtype=np.int16)
            max_chunk_amplitude = np.max(np.abs(chunk_np))
            print(f"Current chunk max amplitude: {max_chunk_amplitude}")  # 추가된 로그
            if max_chunk_amplitude > 500:  # 임계값 조정 가능
                silent_chunks = 0
                is_speaking = True
                print("Voice activity detected")  # 추가된 로그
            elif is_speaking:
                silent_chunks += 1
                print(f"Silent chunk count: {silent_chunks}")  # 추가된 로그

            if is_speaking and (len(buffer) >= 100 or silent_chunks > 10):
                print("Processing audio buffer")  # 추가된 로그
                # ... (나머지 코드는 그대로 유지)

        else:
            time.sleep(0.1)

    print("Audio processing stopped")

def update_subtitle(label, text):
    label.config(text=text)

def create_gui():
    global root, subtitle_label, input_lang_var, output_lang_var, device_var
    root = tk.Tk()
    root.title("YouTube 실시간 번역 자막")
    root.geometry("800x250")

    input_lang_var = tk.StringVar(root)
    input_lang_var.set("영어")  # 기본값
    input_lang_menu = tk.OptionMenu(root, input_lang_var, *LANGUAGES.keys())
    input_lang_menu.pack()

    output_lang_var = tk.StringVar(root)
    output_lang_var.set("한국어")  # 기본값
    output_lang_menu = tk.OptionMenu(root, output_lang_var, *LANGUAGES.keys())
    output_lang_menu.pack()

    devices = get_audio_devices()
    device_var = tk.StringVar(root)
    device_var.set(devices[0] if devices else "No audio devices found")
    device_menu = tk.OptionMenu(root, device_var, *devices)
    device_menu.pack()

    subtitle_label = tk.Label(root, text="자막이 여기에 표시됩니다.", font=("Helvetica", 16), wraplength=780)
    subtitle_label.pack(pady=20)

    start_button = tk.Button(root, text="시작", command=start_listening)
    start_button.pack(side=tk.LEFT, padx=10)

    stop_button = tk.Button(root, text="정지", command=stop_listening)
    stop_button.pack(side=tk.LEFT)

def start_listening():
    global running, translator, input_lang, output_lang
    print("Start button pressed")
    if not running:
        input_lang = LANGUAGES[input_lang_var.get()]
        output_lang = LANGUAGES[output_lang_var.get()]
        translator = GoogleTranslator(source=input_lang, target=output_lang)
        running = True
        Thread(target=audio_stream).start()
        Thread(target=process_audio).start()
        print(f"Listening started. Input: {input_lang}, Output: {output_lang}")
    else:
        print("Already running")

def stop_listening():
    global running
    print("Stop button pressed")
    running = False
    print("Listening stopped")


def audio_callback(in_data, frame_count, time_info, status):
    global running
    print(f"Audio callback: Status: {status}, Frame count: {frame_count}")
    if running:
        audio_queue.put(in_data)
    return (in_data, pyaudio.paContinue)


def audio_stream():
    global sample_rate
    p = pyaudio.PyAudio()
    devices = get_audio_devices()

    if not devices:
        print("오디오 장치가 없습니다.")
        return

    print("사용 가능한 오디오 입력 장치:")
    for i, device in enumerate(devices):
        print(f"{i}: {device['name']}")

    device_index = int(input("사용할 장치의 번호를 입력하세요: "))
    selected_device = devices[device_index]

    device_info = p.get_device_info_by_index(selected_device['index'])
    channels = int(device_info['maxInputChannels'])
    sample_rate = int(device_info['defaultSampleRate'])
    
    print(f"선택된 장치: {device_info['name']}")
    print(f"채널: {channels}, 샘플 레이트: {sample_rate}")

    stream = p.open(format=pyaudio.paInt16,
                channels=channels,
                rate=sample_rate,
                input=True,
                input_device_index=selected_device['index'],
                frames_per_buffer=1024,
                stream_callback=audio_callback)

    stream.start_stream()
    
    while running:
        time.sleep(0.1)
    
    stream.stop_stream()
    stream.close()
    p.terminate()





def main():
    global root
    create_gui()
    root.mainloop()



    

if __name__ == "__main__":
    main()
