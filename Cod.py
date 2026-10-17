import array
import base64
import ctypes
import io
import json
import os
import queue
import sys
import threading
import time
import tkinter as tk
import wave
from ctypes import wintypes

import requests

try:
    import numpy as np
    import sounddevice as sd
except Exception:
    np = sd = None


CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "InterviewHelper")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

SYSTEM_PROMPTS = {
    "ru": "Ты помощник на собеседовании. Отвечай кратко, структурированно и по делу.",
    "en": "You are an interview assistant. Answer concisely, clearly, and to the point.",
}

DEFAULTS = {
    "ui_lang": "ru",
    "api_url": "https://api.openai.com/v1",
    "api_key": "",
    "model": "gpt-4o-mini",
    "system_prompt": SYSTEM_PROMPTS["ru"],
    "opacity": 0.9,
    "topmost": True,
    "stt_model": "",
    "stt_language": "ru",
    "mic_device": "",
    "auto_send": True,
    "direct_audio": False,
    "vad_auto_stop": False,
    "silence_sec": 1.8,
}

I18N = {
    "ru": {
        "topmost": "Поверх",
        "auto_send": "Авто-отпр.",
        "vad_stop": "Авто-стоп",
        "clear": "Очистить",
        "send": "Отправить",
        "mic_start": "🎤 Голос",
        "mic_stop": "⏹ Стоп",
        "hint": "Enter — отправить | Shift+Enter — строка | Ctrl+Shift+M — голос | Ctrl+Shift+H — скрыть",
        "paste": "Вставить",
        "copy": "Копировать",
        "cut": "Вырезать",
        "api_url": "API URL (напр. https://api.openai.com/v1 или Groq/Gemini)",
        "api_key": "API Key",
        "model": "Модель чата (напр. gpt-4o-mini, gemini-2.5-flash)",
        "system_prompt": "Системный промпт",
        "stt_model": "Модель речи STT (пусто = авто: whisper-1 / whisper-large-v3-turbo)",
        "stt_language": "Язык речи (ru, en или пусто для авто)",
        "silence_sec": "Пауза для авто-стопа записи, сек (по умолч. 1.8)",
        "direct_audio": "Прямая отправка аудио в ИИ без STT (Gemini / GPT-4o-audio / OpenRouter)",
        "mic_device": "Устройство записи (микрофон / Стерео микшер)",
        "mic_default": "По умолчанию",
        "save": "Сохранить",
        "warn_capture": "⚠ Не удалось скрыть окно от захвата (нужна Windows 10 2004+).\n",
        "err_no_key": "Укажите API Key в настройках (⚙).\n",
        "err_mic": "Не удалось включить микрофон: {exc}\nПроверьте: Параметры Windows → Конфиденциальность → Микрофон → разрешить доступ.\n",
        "err_rec": "Ошибка записи: {exc}\n",
        "status_rec": "🔴 Слушаю... ({mode}Ctrl+Shift+M — отправить)",
        "status_rec_vad": "авто-стоп по паузе или ",
        "status_short": "Запись слишком короткая",
        "status_stt": "⏳ Распознаю речь и отправляю...",
        "status_queue": "⏳ Отправится сразу после завершения текущего ответа...",
        "err_busy": "Дождитесь завершения текущего ответа.\n",
        "voice_label": "🎤 [Голосовой вопрос]",
        "voice_prompt": "Ответь на вопрос или реплику из этой аудиозаписи.",
        "err_stt_empty": "Речь не распознана, попробуйте ещё раз.\n",
        "err_stt": "Ошибка распознавания: {err}\n",
        "err_req": "\nОшибка: {err}\n\n",
        "stt_chat_prompt": "Расшифруй речь на аудиозаписи дословно. Верни ТОЛЬКО распознанный текст без кавычек и без комментариев.",
        "stt_lang_suffix": " Язык речи: {lang}.",
    },
    "en": {
        "topmost": "On Top",
        "auto_send": "Auto-send",
        "vad_stop": "Auto-stop",
        "clear": "Clear",
        "send": "Send",
        "mic_start": "🎤 Voice",
        "mic_stop": "⏹ Stop",
        "hint": "Enter — send | Shift+Enter — newline | Ctrl+Shift+M — voice | Ctrl+Shift+H — hide",
        "paste": "Paste",
        "copy": "Copy",
        "cut": "Cut",
        "api_url": "API URL (e.g. https://api.openai.com/v1 or Groq/Gemini)",
        "api_key": "API Key",
        "model": "Chat Model (e.g. gpt-4o-mini, gemini-2.5-flash)",
        "system_prompt": "System Prompt",
        "stt_model": "STT Model (empty = auto: whisper-1 / whisper-large-v3-turbo)",
        "stt_language": "Speech Language (en, ru, or empty for auto)",
        "silence_sec": "Silence duration for auto-stop, sec (default 1.8)",
        "direct_audio": "Send audio directly to LLM without STT (Gemini / GPT-4o-audio / OpenRouter)",
        "mic_device": "Input Device (Microphone / Stereo Mix)",
        "mic_default": "Default",
        "save": "Save",
        "warn_capture": "⚠ Failed to exclude window from screen capture (Windows 10 2004+ required).\n",
        "err_no_key": "Please set your API Key in settings (⚙).\n",
        "err_mic": "Failed to start microphone: {exc}\nCheck Windows Settings → Privacy → Microphone → allow desktop apps.\n",
        "err_rec": "Recording error: {exc}\n",
        "status_rec": "🔴 Listening... ({mode}Ctrl+Shift+M — send)",
        "status_rec_vad": "auto-stop on pause or ",
        "status_short": "Recording is too short",
        "status_stt": "⏳ Transcribing and sending...",
        "status_queue": "⏳ Will be sent right after the current response finishes...",
        "err_busy": "Please wait for the current response to finish.\n",
        "voice_label": "🎤 [Voice question]",
        "voice_prompt": "Answer the question or statement in this audio recording.",
        "err_stt_empty": "Speech was not recognized, please try again.\n",
        "err_stt": "Transcription error: {err}\n",
        "err_req": "\nError: {err}\n\n",
        "stt_chat_prompt": "Transcribe the speech in this audio verbatim. Return ONLY the recognized text without quotes or commentary.",
        "stt_lang_suffix": " Speech language: {lang}.",
    },
}


def load_config() -> dict:
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            loaded = json.load(f)
            cfg.update(loaded)
    except (OSError, ValueError):
        pass
    if cfg.get("ui_lang") not in ("ru", "en"):
        cfg["ui_lang"] = "ru"
    return cfg


def save_config(cfg: dict) -> None:
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


IS_WIN = sys.platform == "win32"
WDA_EXCLUDEFROMCAPTURE = 0x00000011
GA_ROOT = 2
MOD_CONTROL, MOD_SHIFT, MOD_NOREPEAT = 0x0002, 0x0004, 0x4000
WM_HOTKEY = 0x0312

if IS_WIN:
    user32 = ctypes.windll.user32
    winmm = ctypes.windll.winmm
    user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetAncestor.restype = wintypes.HWND
    user32.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]
    user32.SetWindowDisplayAffinity.restype = wintypes.BOOL
    user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
    user32.RegisterHotKey.restype = wintypes.BOOL
    user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]


def exclude_from_capture(tk_root: tk.Tk) -> bool:
    if not IS_WIN:
        return False
    tk_root.update_idletasks()
    hwnd = user32.GetAncestor(tk_root.winfo_id(), GA_ROOT)
    return bool(user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE))


class GlobalHotkey(threading.Thread):
    def __init__(self, bindings: dict):
        super().__init__(daemon=True)
        self.bindings = bindings

    def run(self):
        if not IS_WIN:
            return
        callbacks = {}
        for i, (key, callback) in enumerate(self.bindings.items(), start=1):
            if user32.RegisterHotKey(None, i, MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, ord(key.upper())):
                callbacks[i] = callback
        if not callbacks:
            return
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_HOTKEY and msg.wParam in callbacks:
                callbacks[msg.wParam]()


def enable_clipboard(widget, get_lang):
    def on_ctrl_key(event):
        actions = {86: "<<Paste>>", 67: "<<Copy>>", 88: "<<Cut>>"}
        if event.keycode in actions:
            widget.event_generate(actions[event.keycode])
            return "break"
        if event.keycode == 65:
            if isinstance(widget, tk.Entry):
                widget.select_range(0, "end")
            else:
                widget.tag_add("sel", "1.0", "end")
            return "break"

    widget.bind("<Control-KeyPress>", on_ctrl_key)

    def show_menu(event):
        widget.focus_set()
        tr = I18N.get(get_lang(), I18N["ru"])
        menu = tk.Menu(widget, tearoff=0)
        menu.add_command(label=tr["paste"], command=lambda: widget.event_generate("<<Paste>>"))
        menu.add_command(label=tr["copy"], command=lambda: widget.event_generate("<<Copy>>"))
        menu.add_command(label=tr["cut"], command=lambda: widget.event_generate("<<Cut>>"))
        menu.tk_popup(event.x_root, event.y_root)

    widget.bind("<Button-3>", show_menu)


STT_RATE = 16000
MAX_RECORD_SEC = 120
VAD_THRESHOLD = 450

if IS_WIN:
    WAVE_MAPPER = 0xFFFFFFFF
    WAVE_FORMAT_PCM = 1
    CALLBACK_NULL = 0x00000000
    WHDR_DONE = 0x00000001

    class WAVEFORMATEX(ctypes.Structure):
        _fields_ = [
            ("wFormatTag", wintypes.WORD),
            ("nChannels", wintypes.WORD),
            ("nSamplesPerSec", wintypes.DWORD),
            ("nAvgBytesPerSec", wintypes.DWORD),
            ("nBlockAlign", wintypes.WORD),
            ("wBitsPerSample", wintypes.WORD),
            ("cbSize", wintypes.WORD),
        ]

    class WAVEHDR(ctypes.Structure):
        _fields_ = [
            ("lpData", ctypes.c_char_p),
            ("dwBufferLength", wintypes.DWORD),
            ("dwBytesRecorded", wintypes.DWORD),
            ("dwUser", ctypes.c_size_t),
            ("dwFlags", wintypes.DWORD),
            ("dwLoops", wintypes.DWORD),
            ("lpNext", ctypes.c_void_p),
            ("reserved", ctypes.c_size_t),
        ]

    class WAVEINCAPSW(ctypes.Structure):
        _fields_ = [
            ("wMid", wintypes.WORD),
            ("wPid", wintypes.WORD),
            ("vDriverVersion", wintypes.UINT),
            ("szPname", wintypes.WCHAR * 32),
            ("dwFormats", wintypes.DWORD),
            ("wChannels", wintypes.WORD),
            ("wReserved1", wintypes.WORD),
        ]


def list_input_devices() -> list:
    if sd is not None:
        names = []
        try:
            for dev in sd.query_devices():
                if dev["max_input_channels"] > 0 and dev["name"] not in names:
                    names.append(dev["name"])
            if names:
                return names
        except Exception:
            pass

    if IS_WIN:
        names = []
        try:
            count = winmm.waveInGetNumDevs()
            caps = WAVEINCAPSW()
            for i in range(count):
                if winmm.waveInGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
                    if caps.szPname and caps.szPname not in names:
                        names.append(caps.szPname)
        except Exception:
            pass
        return names
    return []


def find_device_index(name: str):
    if not name:
        return None
    if sd is not None:
        try:
            for i, dev in enumerate(sd.query_devices()):
                if dev["max_input_channels"] > 0 and dev["name"] == name:
                    return i
        except Exception:
            pass
    if IS_WIN:
        try:
            count = winmm.waveInGetNumDevs()
            caps = WAVEINCAPSW()
            for i in range(count):
                if winmm.waveInGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
                    if caps.szPname == name or name.startswith(caps.szPname):
                        return i
        except Exception:
            pass
    return None


def _chunk_peak_amplitude(raw_bytes: bytes) -> int:
    if not raw_bytes or len(raw_bytes) < 2:
        return 0
    if np is not None:
        arr = np.frombuffer(raw_bytes, dtype=np.int16)
        if arr.size == 0:
            return 0
        return int(np.abs(arr).mean())
    samples = array.array("h")
    samples.frombytes(raw_bytes[: len(raw_bytes) - (len(raw_bytes) % 2)])
    if not samples:
        return 0
    step = max(1, len(samples) // 200)
    subset = samples[::step]
    return sum(abs(x) for x in subset) // len(subset)


class Recorder:
    def __init__(self, on_silence_callback=None):
        self.stream = None
        self.chunks = []
        self.rate = STT_RATE
        self.on_silence_callback = on_silence_callback
        self.vad_enabled = False
        self.silence_limit_sec = 1.8
        self._spoken = False
        self._last_voice_time = 0.0
        self._start_time = 0.0
        self._silence_triggered = False
        self._hwavein = None
        self._win_running = False
        self._win_thread = None

    def start(self, device_name: str, vad_enabled: bool = False, silence_sec: float = 1.8):
        self.chunks = []
        self.vad_enabled = vad_enabled
        self.silence_limit_sec = max(0.6, float(silence_sec))
        self._spoken = False
        self._silence_triggered = False
        now = time.monotonic()
        self._start_time = now
        self._last_voice_time = now

        if sd is not None:
            device = find_device_index(device_name)
            try:
                self.rate = STT_RATE
                self.stream = self._open_sd(device, self.rate)
            except Exception:
                info = sd.query_devices(device, "input")
                self.rate = int(info["default_samplerate"])
                self.stream = self._open_sd(device, self.rate)
            self.stream.start()
            return

        if IS_WIN:
            self._start_winmm(device_name)
            return

        raise RuntimeError("sounddevice is not installed (pip install sounddevice numpy)")

    def _process_raw_chunk(self, raw_bytes: bytes):
        if not raw_bytes:
            return
        self.chunks.append(raw_bytes)
        if not self.vad_enabled or self._silence_triggered:
            return
        amp = _chunk_peak_amplitude(raw_bytes)
        now = time.monotonic()
        if amp >= VAD_THRESHOLD:
            self._spoken = True
            self._last_voice_time = now
        elif self._spoken and (now - self._last_voice_time) >= self.silence_limit_sec:
            self._silence_triggered = True
            if self.on_silence_callback:
                self.on_silence_callback()

    def _open_sd(self, device, rate):
        def _cb(data, frames, t, status):
            self._process_raw_chunk(bytes(data) if np is None else data.copy().tobytes())

        return sd.InputStream(samplerate=rate, channels=1, dtype="int16", device=device, callback=_cb)

    def _start_winmm(self, device_name: str):
        dev_idx = find_device_index(device_name)
        dev_id = WAVE_MAPPER if dev_idx is None else dev_idx
        self.rate = STT_RATE

        wfx = WAVEFORMATEX()
        wfx.wFormatTag = WAVE_FORMAT_PCM
        wfx.nChannels = 1
        wfx.nSamplesPerSec = self.rate
        wfx.wBitsPerSample = 16
        wfx.nBlockAlign = 2
        wfx.nAvgBytesPerSec = self.rate * 2
        wfx.cbSize = 0

        hwavein = wintypes.HANDLE()
        res = winmm.waveInOpen(ctypes.byref(hwavein), dev_id, ctypes.byref(wfx), 0, 0, CALLBACK_NULL)
        if res != 0:
            raise RuntimeError(f"waveInOpen error code {res}")

        self._hwavein = hwavein
        self._win_running = True
        self._win_thread = threading.Thread(target=self._winmm_loop, daemon=True)
        self._win_thread.start()

    def _winmm_loop(self):
        buf_size = int(self.rate * 2 * 0.1)
        num_bufs = 6
        buffers = [ctypes.create_string_buffer(buf_size) for _ in range(num_bufs)]
        headers = [WAVEHDR() for _ in range(num_bufs)]

        for i in range(num_bufs):
            headers[i].lpData = ctypes.cast(buffers[i], ctypes.c_char_p)
            headers[i].dwBufferLength = buf_size
            winmm.waveInPrepareHeader(self._hwavein, ctypes.byref(headers[i]), ctypes.sizeof(WAVEHDR))
            winmm.waveInAddBuffer(self._hwavein, ctypes.byref(headers[i]), ctypes.sizeof(WAVEHDR))

        winmm.waveInStart(self._hwavein)

        while self._win_running:
            any_done = False
            for i in range(num_bufs):
                if headers[i].dwFlags & WHDR_DONE:
                    any_done = True
                    rec_len = headers[i].dwBytesRecorded
                    if rec_len > 0:
                        raw = buffers[i].raw[:rec_len]
                        self._process_raw_chunk(raw)
                    if self._win_running:
                        headers[i].dwBytesRecorded = 0
                        headers[i].dwFlags &= ~WHDR_DONE
                        winmm.waveInAddBuffer(self._hwavein, ctypes.byref(headers[i]), ctypes.sizeof(WAVEHDR))
            if not any_done:
                time.sleep(0.02)

        winmm.waveInStop(self._hwavein)
        winmm.waveInReset(self._hwavein)
        for i in range(num_bufs):
            winmm.waveInUnprepareHeader(self._hwavein, ctypes.byref(headers[i]), ctypes.sizeof(WAVEHDR))
        winmm.waveInClose(self._hwavein)
        self._hwavein = None

    def stop(self) -> bytes:
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

        if self._win_running:
            self._win_running = False
            if self._win_thread is not None:
                self._win_thread.join(timeout=1.5)
                self._win_thread = None

        if not self.chunks:
            return b""
        pcm_bytes = b"".join(self.chunks)
        min_bytes = int(self.rate * 2 * 0.35)
        if len(pcm_bytes) < min_bytes:
            return b""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(self.rate)
            w.writeframes(pcm_bytes)
        return buf.getvalue()


def resolve_stt_model(cfg: dict) -> str:
    if cfg.get("stt_model", "").strip():
        return cfg["stt_model"].strip()
    url = cfg["api_url"].lower()
    if "generativelanguage.googleapis.com" in url or "openrouter.ai" in url:
        return cfg["model"]
    if "groq.com" in url:
        return "whisper-large-v3-turbo"
    return "whisper-1"


def _transcribe_via_chat_audio(base: str, headers: dict, model: str, lang: str, ui_lang: str, wav_bytes: bytes) -> str:
    tr = I18N.get(ui_lang, I18N["ru"])
    prompt = tr["stt_chat_prompt"] + (tr["stt_lang_suffix"].format(lang=lang) if lang else "")
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": base64.b64encode(wav_bytes).decode("ascii"),
                            "format": "wav",
                        },
                    },
                ],
            }
        ],
    }
    r = requests.post(base + "/chat/completions", headers=headers, json=payload, timeout=(10, 90))
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
    return (r.json()["choices"][0]["message"]["content"] or "").strip()


def transcribe(cfg: dict, wav_bytes: bytes) -> str:
    base = cfg["api_url"].rstrip("/")
    headers = {"Authorization": f"Bearer {cfg['api_key']}"}
    model = resolve_stt_model(cfg)
    lang = cfg.get("stt_language", "").strip()
    ui_lang = cfg.get("ui_lang", "ru")

    if "generativelanguage.googleapis.com" in base.lower() or "openrouter.ai" in base.lower():
        return _transcribe_via_chat_audio(base, headers, model, lang, ui_lang, wav_bytes)

    data = {"model": model}
    if lang:
        data["language"] = lang
    r = requests.post(
        base + "/audio/transcriptions",
        headers=headers,
        data=data,
        files={"file": ("audio.wav", wav_bytes, "audio/wav")},
        timeout=(10, 90),
    )
    if r.status_code == 200:
        return (r.json().get("text") or "").strip()

    if r.status_code in (400, 404, 405, 422):
        try:
            chat_model = cfg["model"]
            if "gpt-4o" in chat_model and "audio" not in chat_model:
                chat_model = "gpt-4o-mini-audio-preview"
            return _transcribe_via_chat_audio(base, headers, chat_model, lang, ui_lang, wav_bytes)
        except Exception:
            pass

    raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")


BG, PANEL, FG, ACCENT, MUTED = "#1e1e2e", "#2a2a3c", "#e6e6f0", "#7aa2f7", "#8a8aa0"


class App:
    def __init__(self):
        self.cfg = load_config()
        self.history = []
        self.events = queue.Queue()
        self.busy = False
        self.pending_auto_send = False
        self.recorder = Recorder(on_silence_callback=lambda: self.events.put(("vad_stop",))) if (sd or IS_WIN) else None
        self.recording = False
        self.transcribing = False
        self.record_timer = None

        self.root = tk.Tk()
        self.root.title("Notes")
        self.root.geometry("560x660+40+40")
        self.root.minsize(400, 440)
        self.root.configure(bg=BG)
        self.root.attributes("-alpha", self.cfg["opacity"])
        self.root.attributes("-topmost", self.cfg["topmost"])
        if IS_WIN:
            self.root.attributes("-toolwindow", True)

        self._build_main()
        self._build_settings()
        self._apply_language()
        self.main_frame.pack(fill="both", expand=True)

        self.capture_hidden = exclude_from_capture(self.root)
        if not self.capture_hidden:
            self._write(self._tr("warn_capture"), "err")

        GlobalHotkey({
            "H": lambda: self.events.put(("toggle",)),
            "M": lambda: self.events.put(("mic",)),
        }).start()
        self.root.bind("<Control-Return>", lambda e: self.send())
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(50, self._poll)
        self.prompt.focus_set()

    def _tr(self, key: str, **kwargs) -> str:
        lang = self.cfg.get("ui_lang", "ru")
        text = I18N.get(lang, I18N["ru"]).get(key, key)
        return text.format(**kwargs) if kwargs else text

    def _btn(self, parent, text, cmd, **kw):
        return tk.Button(parent, text=text, command=cmd, bg=PANEL, fg=FG, relief="flat",
                         activebackground=ACCENT, activeforeground=BG, bd=0, padx=8, pady=2, **kw)

    def _build_main(self):
        f = self.main_frame = tk.Frame(self.root, bg=BG)

        bar = tk.Frame(f, bg=BG)
        bar.pack(side="top", fill="x", padx=6, pady=(6, 2))
        self._btn(bar, "⚙", self.show_settings).pack(side="left")
        self.lang_btn = self._btn(bar, self.cfg["ui_lang"].upper(), self.toggle_language)
        self.lang_btn.pack(side="left", padx=(4, 0))

        tk.Label(bar, text="α", bg=BG, fg=MUTED).pack(side="left", padx=(6, 0))
        self.alpha = tk.Scale(bar, from_=0.3, to=1.0, resolution=0.05, orient="horizontal", length=75,
                              showvalue=False, bg=BG, fg=FG, troughcolor=PANEL, highlightthickness=0,
                              command=self.set_opacity)
        self.alpha.set(self.cfg["opacity"])
        self.alpha.pack(side="left")

        self.topmost = tk.BooleanVar(value=self.cfg["topmost"])
        self.topmost_chk = tk.Checkbutton(bar, variable=self.topmost, command=self.set_topmost, bg=BG, fg=FG,
                                          selectcolor=PANEL, activebackground=BG, activeforeground=FG)
        self.topmost_chk.pack(side="left", padx=2)

        self.clear_btn = self._btn(bar, "", self.clear)
        self.clear_btn.pack(side="right")

        self.vad_var = tk.BooleanVar(value=self.cfg.get("vad_auto_stop", False))
        self.vad_chk = tk.Checkbutton(bar, variable=self.vad_var, command=self.set_vad_auto_stop, bg=BG, fg=FG,
                                      selectcolor=PANEL, activebackground=BG, activeforeground=FG)
        self.vad_chk.pack(side="right", padx=2)

        self.auto_send = tk.BooleanVar(value=self.cfg.get("auto_send", True))
        self.auto_send_chk = tk.Checkbutton(bar, variable=self.auto_send, command=self.set_auto_send, bg=BG, fg=FG,
                                            selectcolor=PANEL, activebackground=BG, activeforeground=FG)
        self.auto_send_chk.pack(side="right", padx=2)

        bottom = tk.Frame(f, bg=BG)
        bottom.pack(side="bottom", fill="x", padx=6, pady=6)
        self.hint = tk.Label(bottom, text="", bg=BG, fg=MUTED, font=("Segoe UI", 8),
                             anchor="w", justify="left")
        self.hint.pack(side="left", fill="x", expand=True)
        self.send_btn = self._btn(bottom, "", self.send)
        self.send_btn.pack(side="right")
        self.mic_btn = self._btn(bottom, "", self.toggle_record)
        self.mic_btn.pack(side="right", padx=(0, 4))
        if self.recorder is None:
            self.mic_btn.config(state="disabled")

        self.prompt = tk.Text(f, height=4, wrap="word", bg=PANEL, fg=FG, insertbackground=FG, bd=0,
                              padx=8, pady=6, font=("Segoe UI", 10))
        self.prompt.pack(side="bottom", fill="x", padx=6)
        self.prompt.bind("<Return>", self._on_enter_key)
        self.prompt.bind("<Shift-Return>", lambda e: None)
        self.prompt.bind("<Control-Return>", lambda e: (self.send(), "break")[1])
        self.prompt.bind("<Button-1>", lambda e: self.prompt.focus_force())

        box = tk.Frame(f, bg=BG)
        box.pack(side="top", fill="both", expand=True, padx=6, pady=4)
        sb = tk.Scrollbar(box)
        sb.pack(side="right", fill="y")
        self.answer = tk.Text(box, height=5, wrap="word", bg=PANEL, fg=FG, bd=0, padx=8, pady=6,
                              state="disabled", yscrollcommand=sb.set, font=("Segoe UI", 10))
        self.answer.pack(side="left", fill="both", expand=True)
        sb.config(command=self.answer.yview)
        self.answer.tag_config("q", foreground=ACCENT)
        self.answer.tag_config("err", foreground="#f7768e")

        get_lang = lambda: self.cfg.get("ui_lang", "ru")
        enable_clipboard(self.prompt, get_lang)
        enable_clipboard(self.answer, get_lang)

    def _on_enter_key(self, event):
        if not (event.state & 0x0001):
            self.send()
            return "break"

    def _build_settings(self):
        f = self.settings_frame = tk.Frame(self.root, bg=BG)
        self.fields = {}
        self.field_labels = {}
        field_keys = [
            "api_url",
            "api_key",
            "model",
            "system_prompt",
            "stt_model",
            "stt_language",
            "silence_sec",
        ]
        get_lang = lambda: self.cfg.get("ui_lang", "ru")
        for key in field_keys:
            lbl = tk.Label(f, text="", bg=BG, fg=MUTED, anchor="w")
            lbl.pack(fill="x", padx=10, pady=(8, 0))
            self.field_labels[key] = lbl
            e = tk.Entry(f, bg=PANEL, fg=FG, insertbackground=FG, bd=0, show="•" if key == "api_key" else "")
            e.insert(0, str(self.cfg.get(key, DEFAULTS.get(key, ""))))
            e.pack(fill="x", padx=10, ipady=4)
            enable_clipboard(e, get_lang)
            self.fields[key] = e

        self.direct_audio_var = tk.BooleanVar(value=self.cfg.get("direct_audio", False))
        self.direct_audio_chk = tk.Checkbutton(
            f,
            variable=self.direct_audio_var,
            bg=BG, fg=FG, selectcolor=PANEL, activebackground=BG, activeforeground=FG, anchor="w"
        )
        self.direct_audio_chk.pack(fill="x", padx=10, pady=(8, 0))

        self.mic_label = tk.Label(f, text="", bg=BG, fg=MUTED, anchor="w")
        self.mic_label.pack(fill="x", padx=10, pady=(8, 0))
        self.input_devices = list_input_devices()
        default_label = self._tr("mic_default")
        self.mic_var = tk.StringVar(value=self.cfg["mic_device"] or default_label)
        self.mic_menu = tk.OptionMenu(f, self.mic_var, default_label, *self.input_devices)
        self.mic_menu.config(bg=PANEL, fg=FG, activebackground=ACCENT, activeforeground=BG, bd=0,
                             highlightthickness=0, anchor="w")
        self.mic_menu["menu"].config(bg=PANEL, fg=FG)
        self.mic_menu.pack(fill="x", padx=10)

        self.save_btn = self._btn(f, "", self.save_settings)
        self.save_btn.pack(pady=14)

    def toggle_language(self):
        old_lang = self.cfg.get("ui_lang", "ru")
        new_lang = "en" if old_lang == "ru" else "ru"
        self.cfg["ui_lang"] = new_lang

        current_prompt = self.fields["system_prompt"].get().strip()
        if current_prompt == SYSTEM_PROMPTS.get(old_lang):
            new_prompt = SYSTEM_PROMPTS[new_lang]
            self.cfg["system_prompt"] = new_prompt
            self.fields["system_prompt"].delete(0, "end")
            self.fields["system_prompt"].insert(0, new_prompt)

        self._apply_language()
        save_config(self.cfg)

    def _apply_language(self):
        lang = self.cfg.get("ui_lang", "ru")
        self.lang_btn.config(text=lang.upper())
        self.topmost_chk.config(text=self._tr("topmost"))
        self.auto_send_chk.config(text=self._tr("auto_send"))
        self.vad_chk.config(text=self._tr("vad_stop"))
        self.clear_btn.config(text=self._tr("clear"))
        self.send_btn.config(text=self._tr("send"))
        self.mic_btn.config(text=self._tr("mic_stop") if self.recording else self._tr("mic_start"))
        if not self.recording and not self.transcribing:
            self.hint.config(text=self._tr("hint"))

        for key, lbl in self.field_labels.items():
            lbl.config(text=self._tr(key))
        self.direct_audio_chk.config(text=self._tr("direct_audio"))
        self.mic_label.config(text=self._tr("mic_device"))
        self.save_btn.config(text=self._tr("save"))

        default_label = self._tr("mic_default")
        current_mic = self.cfg.get("mic_device", "")
        menu = self.mic_menu["menu"]
        menu.delete(0, "end")
        for item in [default_label] + self.input_devices:
            menu.add_command(label=item, command=lambda v=item: self.mic_var.set(v))
        self.mic_var.set(current_mic if current_mic else default_label)

    def set_opacity(self, value):
        self.cfg["opacity"] = float(value)
        self.root.attributes("-alpha", float(value))
        save_config(self.cfg)

    def set_topmost(self):
        self.cfg["topmost"] = self.topmost.get()
        self.root.attributes("-topmost", self.topmost.get())
        save_config(self.cfg)

    def set_auto_send(self):
        self.cfg["auto_send"] = self.auto_send.get()
        save_config(self.cfg)

    def set_vad_auto_stop(self):
        self.cfg["vad_auto_stop"] = self.vad_var.get()
        save_config(self.cfg)

    def toggle_visibility(self):
        if self.root.state() == "withdrawn":
            self.root.deiconify()
            self.root.attributes("-topmost", self.topmost.get())
            exclude_from_capture(self.root)
            self.root.focus_force()
        else:
            self.root.withdraw()

    def show_settings(self):
        self.main_frame.pack_forget()
        self.settings_frame.pack(fill="both", expand=True)

    def save_settings(self):
        for key, entry in self.fields.items():
            val = entry.get().strip()
            if key == "silence_sec":
                try:
                    self.cfg[key] = max(0.5, float(val.replace(",", ".")))
                except ValueError:
                    self.cfg[key] = 1.8
            else:
                self.cfg[key] = val
        self.cfg["direct_audio"] = self.direct_audio_var.get()
        mic = self.mic_var.get()
        default_labels = {I18N["ru"]["mic_default"], I18N["en"]["mic_default"]}
        self.cfg["mic_device"] = "" if mic in default_labels else mic
        save_config(self.cfg)
        self.settings_frame.pack_forget()
        self.main_frame.pack(fill="both", expand=True)
        self.prompt.focus_set()

    def _write(self, text, tag=None):
        self.answer.config(state="normal")
        self.answer.insert("end", text, tag)
        self.answer.see("end")
        self.answer.config(state="disabled")

    def clear(self):
        self.history.clear()
        self.answer.config(state="normal")
        self.answer.delete("1.0", "end")
        self.answer.config(state="disabled")

    def set_status(self, text=None):
        self.hint.config(text=text or self._tr("hint"))

    def toggle_record(self):
        if self.recorder is None or self.transcribing:
            return
        if not self.recording:
            if not self.cfg["api_key"] and "localhost" not in self.cfg["api_url"] and "127.0.0.1" not in self.cfg["api_url"]:
                self._write(self._tr("err_no_key"), "err")
                return
            try:
                self.recorder.start(
                    self.cfg["mic_device"],
                    vad_enabled=self.cfg.get("vad_auto_stop", False),
                    silence_sec=self.cfg.get("silence_sec", 1.8),
                )
            except Exception as exc:
                self._write(self._tr("err_mic", exc=exc), "err")
                return
            self.recording = True
            self.mic_btn.config(text=self._tr("mic_stop"), bg="#f7768e", fg=BG)
            mode_hint = self._tr("status_rec_vad") if self.cfg.get("vad_auto_stop") else ""
            self.set_status(self._tr("status_rec", mode=mode_hint))
            self.record_timer = self.root.after(MAX_RECORD_SEC * 1000, self.toggle_record)
        else:
            self._stop_and_process_recording()

    def _stop_and_process_recording(self):
        if not self.recording:
            return
        if self.record_timer:
            self.root.after_cancel(self.record_timer)
            self.record_timer = None
        self.recording = False
        self.mic_btn.config(text=self._tr("mic_start"), bg=PANEL, fg=FG)
        try:
            wav = self.recorder.stop()
        except Exception as exc:
            self._write(self._tr("err_rec", exc=exc), "err")
            self.set_status()
            return
        if not wav:
            self.set_status(self._tr("status_short"))
            self.root.after(2000, self.set_status)
            return

        if self.cfg.get("direct_audio") and self.cfg.get("auto_send", True):
            self.send_direct_audio(wav)
            return

        self.transcribing = True
        self.mic_btn.config(state="disabled")
        self.set_status(self._tr("status_stt"))
        threading.Thread(target=self._transcribe_worker, args=(wav,), daemon=True).start()

    def _transcribe_worker(self, wav):
        try:
            self.events.put(("stt_done", transcribe(self.cfg, wav)))
        except Exception as exc:
            self.events.put(("stt_error", str(exc)))

    def _stt_finished(self):
        self.transcribing = False
        self.mic_btn.config(state="normal")
        self.set_status()

    def send_direct_audio(self, wav_bytes: bytes):
        if self.busy:
            self._write(self._tr("err_busy"), "err")
            return
        self.busy = True
        self.send_btn.config(state="disabled")
        extra_text = self.prompt.get("1.0", "end").strip()
        self.prompt.delete("1.0", "end")
        label = f"{self._tr('voice_label')}{': ' + extra_text if extra_text else ''}"
        self._write(f"▶ {label}\n", "q")

        prompt_instruction = extra_text or self._tr("voice_prompt")
        user_msg = {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_instruction},
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": base64.b64encode(wav_bytes).decode("ascii"),
                        "format": "wav",
                    },
                },
            ],
        }
        self.history.append({"role": "user", "content": prompt_instruction})
        messages = [{"role": "system", "content": self.cfg["system_prompt"]}] + self.history[:-1][-19:] + [user_msg]
        threading.Thread(target=self._request, args=(messages,), daemon=True).start()

    def send(self):
        question = self.prompt.get("1.0", "end").strip()
        if not question:
            return
        if self.busy:
            self.pending_auto_send = True
            self.set_status(self._tr("status_queue"))
            return
        if not self.cfg["api_key"] and "localhost" not in self.cfg["api_url"] and "127.0.0.1" not in self.cfg["api_url"]:
            self._write(self._tr("err_no_key"), "err")
            return
        self.pending_auto_send = False
        self.busy = True
        self.send_btn.config(state="disabled")
        self.prompt.delete("1.0", "end")
        self._write(f"▶ {question}\n", "q")
        self.history.append({"role": "user", "content": question})
        messages = [{"role": "system", "content": self.cfg["system_prompt"]}] + self.history[-20:]
        threading.Thread(target=self._request, args=(messages,), daemon=True).start()

    def _request(self, messages):
        url = self.cfg["api_url"].rstrip("/") + "/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.cfg['api_key']}"}
        payload = {"model": self.cfg["model"], "messages": messages, "stream": True}
        full = ""
        try:
            with requests.post(url, headers=headers, json=payload, stream=True, timeout=(10, 120)) as r:
                if r.status_code != 200:
                    raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
                r.encoding = "utf-8"
                for line in r.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        delta = json.loads(data)["choices"][0]["delta"].get("content") or ""
                    except (KeyError, IndexError, ValueError):
                        continue
                    if delta:
                        full += delta
                        self.events.put(("chunk", delta))
            self.events.put(("done", full))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    def _poll(self):
        try:
            while True:
                kind, *rest = self.events.get_nowait()
                if kind == "chunk":
                    self._write(rest[0])
                elif kind == "done":
                    self.history.append({"role": "assistant", "content": rest[0]})
                    self._write("\n\n")
                    self._finish()
                elif kind == "error":
                    if self.history:
                        self.history.pop()
                    self._write(self._tr("err_req", err=rest[0]), "err")
                    self._finish()
                elif kind == "toggle":
                    self.toggle_visibility()
                elif kind == "mic":
                    self.toggle_record()
                elif kind == "vad_stop":
                    if self.recording:
                        self._stop_and_process_recording()
                elif kind == "stt_done":
                    self._stt_finished()
                    text = rest[0]
                    if not text:
                        self._write(self._tr("err_stt_empty"), "err")
                    else:
                        if self.prompt.get("1.0", "end").strip():
                            text = " " + text
                        self.prompt.insert("end", text)
                        if self.auto_send.get():
                            self.send()
                elif kind == "stt_error":
                    self._stt_finished()
                    self._write(self._tr("err_stt", err=rest[0]), "err")
        except queue.Empty:
            pass
        self.root.after(50, self._poll)

    def _finish(self):
        self.busy = False
        self.send_btn.config(state="normal")
        self.set_status()
        if self.pending_auto_send and self.prompt.get("1.0", "end").strip():
            self.pending_auto_send = False
            self.send()

    def close(self):
        if self.recording and self.recorder:
            try:
                self.recorder.stop()
            except Exception:
                pass
        save_config(self.cfg)
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    if IS_WIN:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    App().run()