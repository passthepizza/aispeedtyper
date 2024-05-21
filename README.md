# AI Speedtyper - First AI-Assisted Roleplay Macro

Fastest Speedtyper is a powerful macro tool that allows you to automate roleplay interactions in various applications, including Roblox and other Windows-based programs. 

## Features

- Use of screenshots and OCR to capture and process text from the screen
- Customizable bot configuration, including pronouns, weapons/skills, and roleplay excerpts to copy styles
- Adjustable system prompt
- Auto-paste functionality 
- Roblox auto-paste feature
- Chat history

## Prerequisites

Before running the macro, ensure that you have the following:

- Python 3.x installed on your system
- Required Python packages: `pyautogui`, `pyperclip`, `openai==0.28`, `requests`, `Pillow`, `keyboard`, `kivy`

## Installation

1. Clone the repository or download the source code files.
2. Install the required Python packages by running the following command:
   ```
   pip install pyautogui pyperclip openai requests Pillow keyboard kivy
   ```

## Usage

1. Run the `main.py` script using Python:
   ```
   python main.py
   ```
2. The GUI will launch.
3. Configure the bot settings by clicking on the "Bot Configuration" button and adjusting the values in the popup window.
4. Enter your https://groq.com key and https://ocr.space key in the input fields and click "Save API Keys".
5. Ensure that the target application (e.g., Roblox) is open and ready for roleplay.
6. Screenshot the text bubble that you want to process.
7. The bot will generate responses based on the configured settings and the captured text.
8. The responses will be automatically pasted into the target application, simulating your roleplay interactions.

## Customization

- Modify the `bot_config.json` file to customize the bot's pronouns, weapons/skills, roleplay excerpts, and system prompt.
- Adjust the max tokens and stop sequences in the bot configuration to control the length and coherence of the generated responses.
- Toggle the auto-paste and Roblox auto-paste switches in the GUI.

## Disclaimer

Please use this macro responsibly and ensure that it complies with the terms of service and guidelines of the applications you are using it with.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgements

- [Kivy](https://kivy.org/) - Python framework for developing cross-platform GUI applications
- [OpenAI](https://www.openai.com/) - Providing the language model API for generating roleplay responses
- [OCR.Space](https://ocr.space/) - Optical Character Recognition (OCR) service for extracting text from screenshots
