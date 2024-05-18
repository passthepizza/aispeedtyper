import pyautogui
import pyperclip
import openai
import requests
from PIL import ImageGrab
import keyboard
import json
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.switch import Switch
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup

try:
    with open("bot_config.json", "r") as file:
        bot_config = json.load(file)
except FileNotFoundError:
    bot_config = {
        "pronouns": "he/him",
        "weapons_skills": [
            "sword",
            "bow and arrow",
            "magic spells"
        ],
        "excerpts": [
            "Excerpt 1...",
            "Excerpt 2...",
            "Excerpt 3..."
        ],
        "system_prompt": "You are a rp bot designed to engage in short combat roleplay using a quick-style approach. The character you are roleplaying as uses the following pronouns: {pronouns}. Your character has the following weapons/skills: {weapons_skills}. Here are three excerpts to copy the style from:\n\n{excerpt1}\n\n{excerpt2}\n\n{excerpt3}\n\nDon't use metaphors or fancy English terms. Instead of relying on RPG mechanics, you will describe actions and scenes using descriptive language, creating an immersive experience for the users. Refrain from using asterisks to denote actions, and use third person pronouns to refer to yourself. Only do a single action. Don't use I or me but use the specified pronouns. When something is aimed at yourself, step to the side. When fired upon, you'd go in cover and return fire. Describe your actions in the past tense to maintain consistency throughout the roleplay. Use 20 words max. Don't use dialogue at all. Keep responses short.",
    }
    bot_config.setdefault("max_tokens", 30)
    bot_config.setdefault("stop_sequences", ["."])
    with open("bot_config.json", "w") as file:
        json.dump(bot_config, file, indent=4)

bot_config.setdefault("groq_api_key", "")
bot_config.setdefault("ocr_api_key", "")

openai.api_key = bot_config["groq_api_key"]
openai.api_base = "https://api.groq.com/openai/v1"

OCR_API_ENDPOINT = "https://api.ocr.space/parse/image"

def clipboard_screenshot_to_text():
    screenshot = ImageGrab.grabclipboard()
    
    if screenshot is None:
        print("No image found in the clipboard.")
        return ""
    
    screenshot.save("temp_screenshot.png", "PNG")
    
    payload = {
        "apikey": bot_config["ocr_api_key"],
        "language": "eng",
        "isOverlayRequired": False,
        "scale": True,
        "isTable": True,
        "OCREngine": 2
    }
    
    with open("temp_screenshot.png", "rb") as image_file:
        response = requests.post(OCR_API_ENDPOINT, files={"file": image_file}, data=payload)
    
    if response.status_code == 200:
        json_response = response.json()
        if json_response["OCRExitCode"] == 1:
            return json_response["ParsedResults"][0]["ParsedText"].strip()
        else:
            print("OCR Error:", json_response["ErrorMessage"])
            return ""
    else:
        print("API Error:", response.status_code)
        return ""

def generate_response(messages):
    system_prompt = bot_config["system_prompt"].format(
        pronouns=bot_config["pronouns"],
        weapons_skills=", ".join(bot_config["weapons_skills"]),
        excerpt1=bot_config["excerpts"][0],
        excerpt2=bot_config["excerpts"][1],
        excerpt3=bot_config["excerpts"][2]
    )

    messages.insert(0, {"role": "system", "content": system_prompt})

    response = openai.ChatCompletion.create(
        model="llama3-70b-8192",
        messages=messages,
        max_tokens=bot_config["max_tokens"],
        n=1,
        stop=bot_config["stop_sequences"],
        temperature=1,
    )

    return response.choices[0].message['content'].strip()

class LoadingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=20, padding=30)
        loading_label = Label(text="Loading...", font_size=24, color=get_color_from_hex("#ffffff"))
        layout.add_widget(loading_label)

        self.progress_bar = ProgressBar(max=100, size_hint=(1, 0.1))
        layout.add_widget(self.progress_bar)

        self.add_widget(layout)

    def on_enter(self, *args):
        Clock.schedule_once(self.update_progress, 0.1)

    def update_progress(self, dt):
        if self.progress_bar.value < 100:
            self.progress_bar.value += 2
            Clock.schedule_once(self.update_progress, 0.1)
        else:
            Clock.schedule_once(self.transition_to_roleplay, 1)

    def transition_to_roleplay(self, dt):
        self.manager.current = "roleplay"

class ConfigPopup(Popup):
    def __init__(self, save_callback, **kwargs):
        super().__init__(**kwargs)
        self.save_callback = save_callback
        self.title = "Bot Configuration"
        self.size_hint = (0.8, 0.9)
        self.auto_dismiss = False

        scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        layout = BoxLayout(orientation='vertical', spacing=20, padding=30, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        pronouns_label = Label(text="Pronouns:", size_hint=(1, None), height=30, font_name="Roboto-Regular", font_size=16, color=get_color_from_hex("#ffffff"))
        self.pronouns_input = TextInput(text=bot_config["pronouns"], multiline=False, size_hint=(1, None), height=40, background_color=get_color_from_hex("#1f1f1f"), foreground_color=get_color_from_hex("#ffffff"), padding=(10, 10), font_name="Roboto-Regular", font_size=14)
        layout.add_widget(pronouns_label)
        layout.add_widget(self.pronouns_input)

        weapons_skills_label = Label(text="Weapons/Skills (comma-separated):", size_hint=(1, None), height=30, font_name="Roboto-Regular", font_size=16, color=get_color_from_hex("#ffffff"))
        self.weapons_skills_input = TextInput(text=", ".join(bot_config["weapons_skills"]), multiline=False, size_hint=(1, None), height=40, background_color=get_color_from_hex("#1f1f1f"), foreground_color=get_color_from_hex("#ffffff"), padding=(10, 10), font_name="Roboto-Regular", font_size=14)
        layout.add_widget(weapons_skills_label)
        layout.add_widget(self.weapons_skills_input)

        excerpts_label = Label(text="Excerpts:", size_hint=(1, None), height=30, font_name="Roboto-Regular", font_size=16, color=get_color_from_hex("#ffffff"))
        layout.add_widget(excerpts_label)

        for i in range(3):
            excerpt_input = TextInput(text=bot_config["excerpts"][i], multiline=True, size_hint=(1, None), height=100, background_color=get_color_from_hex("#1f1f1f"), foreground_color=get_color_from_hex("#ffffff"), padding=(10, 10), font_name="Roboto-Regular", font_size=14)
            layout.add_widget(excerpt_input)
            setattr(self, f"excerpt_input_{i+1}", excerpt_input)

        system_prompt_label = Label(text="System Prompt:", size_hint=(1, None), height=30, font_name="Roboto-Regular", font_size=16, color=get_color_from_hex("#ffffff"))
        self.system_prompt_input = TextInput(text=bot_config["system_prompt"], multiline=True, size_hint=(1, None), height=200, background_color=get_color_from_hex("#1f1f1f"), foreground_color=get_color_from_hex("#ffffff"), padding=(10, 10), font_name="Roboto-Regular", font_size=14)
        layout.add_widget(system_prompt_label)
        layout.add_widget(self.system_prompt_input)

        max_tokens_label = Label(text="Max Tokens:", size_hint=(1, None), height=30, font_name="Roboto-Regular", font_size=16, color=get_color_from_hex("#ffffff"))
        self.max_tokens_input = TextInput(text=str(bot_config.get("max_tokens", 30)), multiline=False, size_hint=(1, None), height=40, background_color=get_color_from_hex("#1f1f1f"), foreground_color=get_color_from_hex("#ffffff"), padding=(10, 10), font_name="Roboto-Regular", font_size=14)
        layout.add_widget(max_tokens_label)
        layout.add_widget(self.max_tokens_input)

        stop_sequences_label = Label(text="Stop Sequences (comma-separated):", size_hint=(1, None), height=30, font_name="Roboto-Regular", font_size=16, color=get_color_from_hex("#ffffff"))
        self.stop_sequences_input = TextInput(text=", ".join(bot_config.get("stop_sequences", [".", "!", "?"])), multiline=False, size_hint=(1, None), height=40, background_color=get_color_from_hex("#1f1f1f"), foreground_color=get_color_from_hex("#ffffff"), padding=(10, 10), font_name="Roboto-Regular", font_size=14)
        layout.add_widget(stop_sequences_label)
        layout.add_widget(self.stop_sequences_input)

        save_button = Button(text="Save", size_hint=(1, None), height=50, on_press=self.save_config, background_color=get_color_from_hex("#2196F3"), font_name="Roboto-Regular", font_size=18)
        save_button.background_normal = ""
        save_button.background_down = ""
        layout.add_widget(save_button)

        scroll_view.add_widget(layout)
        self.content = scroll_view

    def save_config(self, instance):
        bot_config["pronouns"] = self.pronouns_input.text
        bot_config["weapons_skills"] = [item.strip() for item in self.weapons_skills_input.text.split(",")]
        bot_config["excerpts"] = [getattr(self, f"excerpt_input_{i+1}").text for i in range(3)]
        bot_config["system_prompt"] = self.system_prompt_input.text
        bot_config["max_tokens"] = int(self.max_tokens_input.text)
        bot_config["stop_sequences"] = [item.strip() for item in self.stop_sequences_input.text.split(",")]

        self.save_callback(bot_config)
        self.dismiss()

class RoleplayScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.messages = []
        self.last_ocr_text = ""
        self.screenshot_detection_enabled = True
        self.auto_paste_enabled = True
        self.roblox_auto_paste_enabled = True

        layout = self.build_layout()
        self.add_widget(layout)

        Clock.schedule_interval(self.process_screenshot, 1)

    def build_layout(self):
        layout = BoxLayout(orientation='vertical', spacing=20, padding=30)
        
        title_label = Label(text="Fastest Speedtyper", font_size=30, size_hint=(1, 0.1), font_name="Roboto-Bold", color=get_color_from_hex("#ffffff"))
        layout.add_widget(title_label)
        
        self.chat_history = ScrollView(size_hint=(1, 0.7))
        self.chat_history_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        self.chat_history_layout.bind(minimum_height=self.chat_history_layout.setter('height'))
        self.chat_history.add_widget(self.chat_history_layout)
        layout.add_widget(self.chat_history)
        
        reset_button = Button(text="Reset Conversation", size_hint=(1, 0.1), on_press=self.reset_conversation, background_color=get_color_from_hex("#4CAF50"), font_name="Roboto-Regular", font_size=18)
        reset_button.background_normal = ""
        reset_button.background_down = ""
        layout.add_widget(reset_button)
        
        screenshot_detection_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.1))
        screenshot_detection_label = Label(text="Screenshot Detection:", size_hint=(0.8, 1), font_name="Roboto-Regular", font_size=16, color=get_color_from_hex("#ffffff"))
        self.screenshot_detection_switch = Switch(active=True, size_hint=(0.2, 1))
        self.screenshot_detection_switch.bind(active=self.toggle_screenshot_detection)
        screenshot_detection_layout.add_widget(screenshot_detection_label)
        screenshot_detection_layout.add_widget(self.screenshot_detection_switch)
        layout.add_widget(screenshot_detection_layout)
        
        auto_paste_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.1))
        auto_paste_label = Label(text="Auto Paste:", size_hint=(0.8, 1), font_name="Roboto-Regular", font_size=16, color=get_color_from_hex("#ffffff"))
        self.auto_paste_switch = Switch(active=True, size_hint=(0.2, 1))
        self.auto_paste_switch.bind(active=self.toggle_auto_paste)
        auto_paste_layout.add_widget(auto_paste_label)
        auto_paste_layout.add_widget(self.auto_paste_switch)
        layout.add_widget(auto_paste_layout)
        
        roblox_auto_paste_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.1)) 
        roblox_auto_paste_label = Label(text="Roblox Auto Paste:", size_hint=(0.8, 1), font_name="Roboto-Regular", font_size=16, color=get_color_from_hex("#ffffff"))
        self.roblox_auto_paste_switch = Switch(active=True, size_hint=(0.2, 1))
        self.roblox_auto_paste_switch.bind(active=self.toggle_roblox_auto_paste)
        roblox_auto_paste_layout.add_widget(roblox_auto_paste_label)
        roblox_auto_paste_layout.add_widget(self.roblox_auto_paste_switch)
        layout.add_widget(roblox_auto_paste_layout)
        
        config_button = Button(text="Bot Configuration", size_hint=(1, 0.1), on_press=self.open_config_popup, background_color=get_color_from_hex("#2196F3"), font_name="Roboto-Regular", font_size=18)
        config_button.background_normal = ""
        config_button.background_down = ""
        layout.add_widget(config_button)
        
        api_keys_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.1))
        groq_api_key_label = Label(text="Groq API Key:", size_hint=(0.5, 1), font_name="Roboto-Regular", font_size=16, color=get_color_from_hex("#ffffff"))
        self.groq_api_key_input = TextInput(text=bot_config["groq_api_key"], multiline=False, size_hint=(0.5, 1), background_color=get_color_from_hex("#1f1f1f"), foreground_color=get_color_from_hex("#ffffff"), padding=(10, 10), font_name="Roboto-Regular", font_size=14)
        api_keys_layout.add_widget(groq_api_key_label)
        api_keys_layout.add_widget(self.groq_api_key_input)
        layout.add_widget(api_keys_layout)
        
        ocr_api_key_label = Label(text="OCR API Key:", size_hint=(0.5, 1), font_name="Roboto-Regular", font_size=16, color=get_color_from_hex("#ffffff"))
        self.ocr_api_key_input = TextInput(text=bot_config["ocr_api_key"], multiline=False, size_hint=(0.5, 1), background_color=get_color_from_hex("#1f1f1f"), foreground_color=get_color_from_hex("#ffffff"), padding=(10, 10), font_name="Roboto-Regular", font_size=14)
        api_keys_layout.add_widget(ocr_api_key_label)
        api_keys_layout.add_widget(self.ocr_api_key_input)
        
        save_button = Button(text="Save API Keys", size_hint=(1, 0.1), on_press=self.save_api_keys, background_color=get_color_from_hex("#2196F3"), font_name="Roboto-Regular", font_size=18)
        save_button.background_normal = ""
        save_button.background_down = ""
        layout.add_widget(save_button)

        return layout
    
    def process_screenshot(self, dt):
        if not self.screenshot_detection_enabled:
            return
        
        ocr_text = clipboard_screenshot_to_text()
        
        if ocr_text == "" or ocr_text == self.last_ocr_text:
            return
        
        self.last_ocr_text = ocr_text
        
        ocr_label = Label(text=ocr_text, size_hint_y=None, height=40, halign='right', valign='middle', text_size=(self.chat_history.width - 20, None), padding=(10, 10), font_name="Roboto-Regular", font_size=14, color=get_color_from_hex("#ffffff"))
        self.chat_history_layout.add_widget(ocr_label)
        
        self.messages.append({"role": "user", "content": ocr_text})
        
        response = generate_response(self.messages)
        
        bot_response = Label(text=response, size_hint_y=None, height=40, halign='left', valign='middle', text_size=(self.chat_history.width - 20, None), padding=(10, 10), font_name="Roboto-Regular", font_size=14, color=get_color_from_hex("#ffffff"))
        self.chat_history_layout.add_widget(bot_response)
        
        self.messages.append({"role": "assistant", "content": response})
        
        self.chat_history.scroll_to(bot_response)
        
        pyperclip.copy(response)
        
        if self.auto_paste_enabled:
            pyautogui.hotkey('ctrl', 'v')
            pyautogui.press('enter')
        
        if self.roblox_auto_paste_enabled:
            pyautogui.hotkey('/', 'ctrl', 'v')
            pyautogui.press('enter')
    
    def reset_conversation(self, instance):
        self.messages = []
        self.chat_history_layout.clear_widgets()
        self.last_ocr_text = ""
    
    def toggle_screenshot_detection(self, instance, value):
        self.screenshot_detection_enabled = value
    
    def toggle_auto_paste(self, instance, value):
        self.auto_paste_enabled = value
        if value:
            self.roblox_auto_paste_switch.active = False
    
    def toggle_roblox_auto_paste(self, instance, value):
        self.roblox_auto_paste_enabled = value
        if value:
            self.auto_paste_switch.active = False
    
    def open_config_popup(self, instance):
        popup = ConfigPopup(save_callback=self.save_config)
        popup.open()
    
    def save_config(self, updated_config):
        global bot_config
        bot_config = updated_config
        with open("bot_config.json", "w") as file:
            json.dump(bot_config, file, indent=4)
    
    def save_api_keys(self, instance):
        bot_config["groq_api_key"] = self.groq_api_key_input.text
        bot_config["ocr_api_key"] = self.ocr_api_key_input.text
        with open("bot_config.json", "w") as file:
            json.dump(bot_config, file, indent=4)
        openai.api_key = bot_config["groq_api_key"]

class RoleplayApp(App):
    def build(self):
        Window.size = (800, 600)
        Window.clearcolor = get_color_from_hex("#121212")

        sm = ScreenManager()
        sm.add_widget(LoadingScreen(name="loading"))
        sm.add_widget(RoleplayScreen(name="roleplay"))

        return sm

if __name__ == "__main__":
    RoleplayApp().run()
