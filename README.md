# Interview Helper (AI Overlay for Interviews)

[**🇬🇧 English**](#english) | [**🇷🇺 Русский**](#русский)

---

<a name="english"></a>
## 🇬🇧 English

**Interview Helper** is a lightweight, stealthy desktop overlay for Windows that connects to any OpenAI-compatible LLM API (OpenAI, Groq, Google Gemini, OpenRouter, or local models) with instant voice input and real-time streaming responses.

### ✨ Key Features
- **Invisible to Screen Capture**: Uses the native Windows API (`SetWindowDisplayAffinity` with `WDA_EXCLUDEFROMCAPTURE`) so the window is completely invisible in OBS, Discord, Zoom, Microsoft Teams, and Google Meet screen shares (requires Windows 10 build 2004+ or Windows 11).
- **Stealth Taskbar Mode**: Runs as a tool window (`-toolwindow`) so it does not appear on the Windows taskbar or in `Alt+Tab`.
- **Instant Voice Input + Auto-Send**:
  - Works out of the box on Windows via native `winmm.dll` audio capture (no external audio drivers required), or via `sounddevice` if installed.
  - Supports **Auto-Send** (immediately sends recognized speech to the AI) and **Hands-Free VAD Auto-Stop** (automatically stops recording and sends when you pause speaking).
  - Supports standard Whisper endpoints (`/audio/transcriptions`), automatic multimodal fallback (`/chat/completions` with `input_audio`), and **Direct Audio Mode** (sends raw audio directly to Gemini / GPT-4o-audio without intermediate STT).
  - Can capture either your microphone or system audio ("Stereo Mix") to listen to the interviewer directly.
- **Bilingual UI (`RU` / `EN`)**: Switch between Russian and English interface languages on the fly with a single click in the top bar.
- **Global Hotkeys**:
  - `Ctrl + Shift + H` — Show / hide the overlay window from anywhere.
  - `Ctrl + Shift + M` — Start / stop voice recording from anywhere.

### 🚀 Getting Started

#### 1. Requirements
- **OS**: Windows 10 (version 2004 / build 19041 or newer) or Windows 11.
- **Python**: Python 3.9+

#### 2. Installation
```bash
git clone https://github.com/your-username/interview-helper.git
cd interview-helper
pip install -r requirements.txt
```
*(Optional: `pip install sounddevice numpy` for low-latency PortAudio capture; on Windows, built-in `winmm` works without them).*

#### 3. Run the Application
```bash
python Cod.py
```

#### 4. Build Standalone `.exe`
```bash
pip install pyinstaller
pyinstaller InterviewHelper.spec
```
The compiled executable will appear in `dist/InterviewHelper.exe`.

### ⌨️ Controls & Shortcuts
| Shortcut / Control | Action |
| :--- | :--- |
| `Ctrl + Shift + H` | Global hotkey: Hide / show the overlay window |
| `Ctrl + Shift + M` | Global hotkey: Start / stop voice recording |
| `Enter` | Send text prompt to AI |
| `Shift + Enter` | Insert a new line in the prompt box |
| `RU` / `EN` button | Switch interface language (Russian / English) |
| `⚙` button | Open API, model, and audio settings |

### 🔧 Supported API Providers
| Provider | Base API URL (`api_url`) | Recommended Chat Model | Recommended STT Model |
| :--- | :--- | :--- | :--- |
| **OpenAI** | `https://api.openai.com/v1` | `gpt-4o-mini` / `gpt-4o` | `whisper-1` |
| **Groq** | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` | `whisper-large-v3-turbo` |
| **Google Gemini** | `https://generativelanguage.googleapis.com/v1beta/openai` | `gemini-2.5-flash` | *(Auto / Multimodal)* |
| **OpenRouter** | `https://openrouter.ai/api/v1` | `openai/gpt-4o-mini` | *(Auto / Multimodal)* |

---

<a name="русский"></a>
## 🇷🇺 Русский

**Interview Helper** — компактное оверлей-приложение для Windows для общения с ИИ (любой OpenAI-совместимый API: OpenAI, Groq, Google Gemini, OpenRouter или локальные модели) с голосовым вводом и мгновенной отправкой запросов.

### ✨ Основные возможности
- **Невидимость для записи экрана (OBS, Discord, Zoom, Teams)**: использует системный флаг Windows API `SetWindowDisplayAffinity(WDA_EXCLUDEFROMCAPTURE)` — окно отображается только на вашем физическом мониторе и полностью скрыто на демонстрации экрана и стримах (требуется Windows 10 версии 2004 / build 19041 и новее или Windows 11).
- **Скрытие из панели задач и `Alt+Tab`**: окно работает в режиме `toolwindow` под нейтральным заголовком `Notes`.
- **Голосовой ввод и мгновенная отправка**:
  - Запись звука работает на Windows «из коробки» через системную библиотеку `winmm.dll` (даже без установки `sounddevice` и `numpy`).
  - Режим **Авто-отпр.** сразу отправляет распознанную речь в ИИ без нажатия кнопок.
  - Режим **Авто-стоп (VAD)** автоматически завершает запись и отправляет запрос, когда вы делаете паузу в речи.
  - Поддержка как классического Whisper (`/audio/transcriptions`), так и мультимодального режима (`input_audio` в `/chat/completions`), включая опцию **прямой отправки аудио в ИИ без STT**.
  - Поддержка записи со «Стерео микшера» для распознавания вопросов собеседника напрямую из системы.
- **Двуязычный интерфейс (`RU` / `EN`)**: мгновенное переключение между русским и английским языками кнопкой на верхней панели.
- **Глобальные горячие клавиши**:
  - `Ctrl + Shift + H` — Скрыть / показать окно поверх всех программ.
  - `Ctrl + Shift + M` — Начать / остановить запись голоса из любого окна.

### 🚀 Установка и запуск

#### 1. Системные требования
- **ОС**: Windows 10 (версия 2004 / сборка 19041 и выше) или Windows 11.
- **Python**: 3.9 или новее.

#### 2. Установка зависимостей
```bash
git clone https://github.com/your-username/interview-helper.git
cd interview-helper
pip install -r requirements.txt
```

#### 3. Запуск
```bash
python Cod.py
```

#### 4. Сборка в один `.exe` файл
```bash
pip install pyinstaller
pyinstaller InterviewHelper.spec
```
Готовый файл появится по пути `dist/InterviewHelper.exe`.

### ⌨️ Горячие клавиши и управление
| Клавиша / Кнопка | Действие |
| :--- | :--- |
| `Ctrl + Shift + H` | Глобальный хоткей: скрыть или показать окно |
| `Ctrl + Shift + M` | Глобальный хоткей: старт / стоп записи голоса и отправка |
| `Enter` | Отправить сообщение в ИИ |
| `Shift + Enter` | Перенос строки в поле ввода |
| Кнопка `RU` / `EN` | Переключение языка интерфейса (Русский / Английский) |
| Кнопка `⚙` | Настройки API-ключа, модели, микрофона и авто-стопа |

### 📄 Лицензия / License
Распространяется под лицензией [MIT](LICENSE). / Distributed under the [MIT License](LICENSE).
