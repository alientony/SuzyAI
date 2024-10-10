import openai
from os import system
import speech_recognition as sr
import sys
import configparser
import whisper
import warnings
import time
import os
import numpy as np
import torch
import json
import webbrowser
import subprocess
import re
import sympy as sp
torch.cuda.is_available()
from urllib.parse import urlencode
from datetime import datetime, timedelta
import requests
import pyttsx3
import threading
import queue
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, QTextEdit, QPushButton, QDesktopWidget, QSystemTrayIcon, QMenu, QAction, QApplication, QMessageBox, QLineEdit
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QTimer, QUrl, QCoreApplication, QPropertyAnimation, QRect, QEasingCurve, QObject, QThread, QPoint
from PyQt5.QtGui import QPixmap, QIcon, QDesktopServices, QPalette, QColor, QBrush, QCursor, QMovie
import PyQt5.QtWidgets
import PyQt5.QtCore
import PyQt5.QtGui
from pathlib import Path
import datetime
from datetime import datetime
import mimetypes
import schedule
from urllib.request import pathname2url
from urllib.parse import quote
import pythoncom
import pygame
import configparser
import tkinter as tk
from tkinter import filedialog
import sympy as sp
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget


# Initialize pygame mixer
pygame.mixer.init()

print(np.__version__)
print(np.__file__)

pythoncom.CoInitialize()







# Define the path to the configuration file
config_file_path = 'app_config.ini'

# Default settings
default_settings = {
    'OpenAI': {
        'api_key': 'your_openai_api_key_here',
        'assistant_id': 'your_assistant_id_here'
    },
    'Application': {
        'wake_word': 'computer',
        'index_directory_path': 'C:/',
        'default_style': 'default',
        'person_name': 'Bob',
        'soundon': 'True',
        'weather_api_key': 'Weather_API_here',
        'whispermodels_path':'.\models',

    }
}

def create_config_file(path, settings):
    """
    Create a new configuration file with default settings.
    """
    config = configparser.ConfigParser()
    config.read_dict(settings)
    with open(path, 'w') as configfile:
        config.write(configfile)

def load_settings(path):
    """
    Load settings from the configuration file. If the file doesn't exist,
    create it with default settings.
    """
    if not os.path.exists(path):
        create_config_file(path, default_settings)

    config = configparser.ConfigParser()
    config.read(path)
    return config

def get_setting(config, section, option, default=None):
    """
    Retrieve a specific setting value with a fallback to default.
    """
    try:
        return config.get(section, option)
    except (configparser.NoSectionError, configparser.NoOptionError):
        return default

# Load settings from config file or create it if it doesn't exist
config = load_settings(config_file_path)

# Example usage of getting settings
openai.api_key = get_setting(config, 'OpenAI', 'api_key')
assistant_id = get_setting(config, 'OpenAI', 'assistant_id')
wake_word = get_setting(config, 'Application', 'wake_word', 'computer')  # With default fallback
index_directory_path = get_setting(config, 'Application', 'index_directory_path', 'C:/')  # With default fallback
default_style = get_setting(config, 'Application', 'default_style', 'default')  # With default fallback
person_name = get_setting(config, 'Application', 'person_name', 'Ask for my name')
soundON = get_setting(config, 'Application', 'soundON', True)  # With default fallback
WhisperModels_Path = get_setting(config, 'Application', 'WhisperModels_Path', './')  # With default fallback
tiny_model_path = os.path.expanduser(f'{WhisperModels_Path}/tiny.en.pt')
base_model_path = os.path.expanduser(f'{WhisperModels_Path}/medium.en.pt')
def load_config():
    config = configparser.ConfigParser()
    config.read(config_file_path)
    return config

def save_config(config):
    with open(config_file_path, 'w') as configfile:
        config.write(configfile)


# Function to load the Whisper model with error handling
def load_model_with_prompt(model_name, model_path_variable):
    try:
        model = whisper.load_model(model_path_variable)
        return model
    except RuntimeError as e:
        print(e)
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        new_model_path = filedialog.askdirectory(title=f"Select folder containing {model_name} model")
        if new_model_path:
            model_path_variable = os.path.join(new_model_path, f"{model_name}.pt")
            # Save the new model path to the configuration file
            save_model_path(config, model_name, new_model_path)
            try:
                model = whisper.load_model(model_path_variable)
                return model
            except RuntimeError as e:
                print(e)
                sys.exit(f"Failed to load {model_name} model from the selected directory.")
        else:
            sys.exit(f"{model_name} model not found and no folder selected. Exiting.")


# Function to save the new model path
def save_model_path(config, model_name, new_model_path):
    config.set('Application', 'WhisperModels_Path', new_model_path)
    save_config(config)
        
        
# Set your OpenAI API key here

r = sr.Recognizer()

tiny_model = load_model_with_prompt("tiny.en", tiny_model_path)
base_model = load_model_with_prompt("base", base_model_path)
listening_for_wake_word = True
source = sr.Microphone()
warnings.filterwarnings("ignore", category=UserWarning, module='whisper.transcribe', lineno=114)
not_continuing_convo = False
last_command_time = time.time()  # Global variable to keep track of the last command time
last_processed_message_id = None
mutedtalking = False
listen_to_me = False
def save_thread_id(thread_id, filename="thread_id.txt"):
    with open(filename, "w") as file:
        file.write(thread_id)

def load_thread_id(filename="thread_id.txt"):
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return file.read().strip()
    return None

# Load or create a new thread
thread_id = load_thread_id()
if not thread_id:
    thread = openai.beta.threads.create()
    print(thread)
    thread_id = thread.id
    save_thread_id(thread_id)

def load_seen_animations(filename):
    try:
        with open(filename, "r") as file:
            return set(line.strip() for line in file)
    except FileNotFoundError:
        return set()

def display_animation(animations_with_counts):
    total_words = 0
    seen_animations = load_seen_animations("emotions_list.txt")  # Load previously seen animations

    for anim, word_count in animations_with_counts:
        total_words += word_count
        delay = (total_words / 250) * 60  # Assuming 210 words per minute
        time.sleep(delay)

        # Check if this animation is new
        if anim not in seen_animations:
            seen_animations.add(anim)
            # Append new animation to the file
            with open("emotions_list.txt", "a") as file:
                file.write(anim + "\n")

        # Put the animation label in the queue
        animation_queue.put(anim)


def load_styles(style_dir='styles'):
    styles = {}
    if not os.path.exists(style_dir):
        os.makedirs(style_dir)

    for file in os.listdir(style_dir):
        if file.endswith('.json'):
            with open(os.path.join(style_dir, file), 'r') as f:
                style_name = os.path.splitext(file)[0]
                styles[style_name] = json.load(f)
               
    return styles


# Global variable to store styles
STYLES = load_styles()

from PyQt5.QtWidgets import QComboBox
import os

class SettingsWindow(QWidget):
    styleChanged = pyqtSignal()
    def __init__(self):
        super().__init__()
        
        self.config = load_config()
        self.gifLabel = QLabel(self)
        self.movie = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Settings")
        self.layout = QVBoxLayout(self)

        self.styleComboBox = QComboBox(self)
        self.styleComboBox.addItems(STYLES.keys())
        self.styleComboBox.currentIndexChanged.connect(self.changeStyle)
        self.layout.addWidget(QLabel("Select Style:"))
        self.layout.addWidget(self.styleComboBox)
        
        
        # Add UI elements for each settingh setting
        self.add_setting_input("OpenAI API Key:", 'OpenAI', 'api_key')
        self.add_setting_input("Assistant ID:", 'OpenAI', 'assistant_id')
        self.add_setting_input("Wake Word:", 'Application', 'wake_word')
        self.add_setting_input("Index Directory:", 'Application', 'index_directory_path')

        
        
        # Update Index Button
        self.updateIndexButton = QPushButton("Update Index", self)
        self.updateIndexButton.clicked.connect(self.triggerIndexUpdate)
        self.layout.addWidget(self.updateIndexButton)
        
        
        self.add_setting_input("WhisperModels:", 'Application', 'WhisperModels_Path')
        self.add_setting_input("Your Name:", 'Application', 'person_name')

        # Sound Toggle Button
        self.soundToggleButton = QPushButton("Toggle Sound", self)
        self.soundToggleButton.clicked.connect(self.toggleSound)
        self.layout.addWidget(self.soundToggleButton)    
        
        self.setLayout(self.layout)
        self.setGeometry(300, 300, 400, 200)

    def closeEvent(self, event):
        # Ignore the close event
        event.ignore()
        self.hide()

    def toggleSound(self):
        global soundON
        soundON = not soundON  # Toggle the soundON variable
        self.config.set('Application', 'soundON', str(soundON))  # Update the config
        self.updateSoundToggleButton()  # Update the button's appearance
        
        print(f"Sound toggled: {'ON' if soundON else 'OFF'}")  # For demonstration

    def updateSoundToggleButton(self):
        if soundON:
            self.soundToggleButton.setStyleSheet("background-color: green; color: black;")
            self.soundToggleButton.setText("Sound ON")
        else:
            self.soundToggleButton.setStyleSheet("background-color: red; color: black;")
            self.soundToggleButton.setText("Sound OFF")


    def add_setting_input(self, label_text, section, option):
        layout = QHBoxLayout()
        label = QLabel(label_text, self)
        lineEdit = QLineEdit(self)
        lineEdit.setText(self.config.get(section, option, fallback=""))
        saveButton = QPushButton("Save", self)
        saveButton.clicked.connect(lambda: self.save_setting(section, option, lineEdit.text()))
        layout.addWidget(label)
        layout.addWidget(lineEdit)
        layout.addWidget(saveButton)
        self.layout.addLayout(layout)

    def add_update_index_button(self):
        # Create the Update Index button and add it to the layout
        self.updateIndexButton = QPushButton("Update Index", self)
        self.updateIndexButton.clicked.connect(self.triggerIndexUpdate)
        self.layout.addWidget(self.updateIndexButton)
        
    def save_setting(self, section, option, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, value)
        save_config(self.config)
        QMessageBox.information(self, "Settings Updated", f"{option} updated successfully.")
        
    def add_style_combobox(self):
        # Assuming STYLES is a dictionary where keys are style names
        self.styleComboBox = QComboBox(self)
        self.styleComboBox.addItems(list(STYLES.keys()))
        self.styleComboBox.currentIndexChanged.connect(self.changeStyle)
        self.layout.addWidget(QLabel("Select Style:"))
        self.layout.addWidget(self.styleComboBox)
        
    def changeStyle(self, index):
        style_name = self.styleComboBox.itemText(index)
        style_details = STYLES[style_name]
        
        # Update the default_style variable and save to config
        self.config.set('Application', 'default_style', style_name)
        save_config(self.config)
        
        # Apply the stylesheet
        style_sheet = style_details.get('stylesheet', '')
        QApplication.instance().setStyleSheet(style_sheet)
        
        # Handle background settings
        bg = style_details.get('background', {})
        if bg.get('color'):
            color = bg['color']
            QApplication.instance().setPalette(QPalette(QColor(color)))
        if 'image' in bg:
            image_path = bg['image']
            if os.path.exists(image_path):
                if image_path.lower().endswith('.gif'):
                    # In the __init__ method of LabelUpdater
                    self.movie = QMovie(image_path)  # Initialize the movie object

                    
                    
                    
                    
                    self.movie.start()
                else:
                    # Use QPixmap for static images
                    pixmap = QPixmap(image_path)
                    brush = QBrush()

                    if bg.get('mode') == 'fit':
                        # Scale pixmap to fill the screen while keeping aspect ratio
                        brush.setTexture(pixmap.scaled(QApplication.instance().primaryScreen().size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
                    else:
                        # Use the pixmap as-is for the brush texture
                        brush.setTexture(pixmap)

                    palette = QApplication.instance().palette()
                    palette.setBrush(QPalette.Window, brush)
                    QApplication.instance().setPalette(palette)
            else:
                print(f"Background image file does not exist: {image_path}")
        else:
            print("The 'image' key is missing in the background configuration.")
        self.styleChanged.emit() 
        load_and_update_sound_effects(style_name)
    def on_frame_changed(self):
        if self.movie:
            self.label.setMovie(self.movie)

    def triggerIndexUpdate(self):
        index_directory_path = get_setting(config, 'Application', 'index_directory_path', 'C:/')  # With default fallback
        threading.Thread(target=weekly_indexing_task, daemon=True).start()
        

    def saveIndexPath(self):
        global index_directory_path
        index_directory_path = self.indexPathLineEdit.text()
        print("Index directory updated to:", index_directory_path)  # For demonstration



command_ready = False
animation_queue = queue.Queue()

# Create a new QObject to hold signals
class Communicator(QObject):
    show_draft_email_signal = pyqtSignal(str)

class WorkerThread(QThread):
    showDraftEmailSignal = pyqtSignal(str)

    def run(self):
        # Simulate generating draft email content
        draft = "This is a simulated draft email."
        self.showDraftEmailSignal.emit(draft)



class LabelUpdater(QWidget):
    showDraftEmailSignal = pyqtSignal(str)
    global listen_to_me
    def __init__(self, parent=None):
        super(LabelUpdater, self).__init__(parent)
        self.default_style = default_style
        self.movie = None
        self.settingsWindow = SettingsWindow()
        self.settingsWindow.styleChanged.connect(self.updateDefaultStyle)
        self.movie = None
        # Connect the signal
        self.default_style = default_style
        self.showDraftEmailSignal.connect(self.showDraftEmailWidget)
        self.communicator = Communicator()
        self.communicator.show_draft_email_signal.connect(self.showDraftEmailWidget)        
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.setWindowIcon(QIcon('./icons/chat.png'))  # Replace with the path to your icon file
        # Chat history display - using ClickableTextEdit now
        self.chat_history = QTextBrowser(self)
        self.chat_history.setReadOnly(True)
        self.chat_history.setOpenExternalLinks(True)

        # Link display area
        
        self.link_display = QTextBrowser(self)  # A read-only area for links
        self.link_display.setOpenExternalLinks(True)
        self.link_display.setOpenLinks(False)
        self.link_display.setReadOnly(True)
        self.link_display.anchorClicked.connect(self.handle_link_clicked)  # Connect to a custom slot
        
        # Message input area
        self.message_input = QTextEdit(self)
        self.message_input.setFixedHeight(50)  # Adjust height as needed

        # Send button
        self.send_button = QPushButton('Send', self)
        self.send_button.clicked.connect(self.handle_send_button)
        
        # Microphone button
        self.mic_button = QPushButton(self)
        self.mic_button.setIcon(QIcon('./icons/mic_red.png'))  # Assuming starting with red icon
        self.mic_button.setStyleSheet("QPushButton {border-radius : 25; border : 2px solid black;}")  # Adjust size for circle
        self.mic_button.setCheckable(True)
        self.mic_button.clicked.connect(self.handle_mic_button)

        self.settingsWindow = None  # Initialize the reference to None
        self.applyDefaultStyle()
        self.initUI()
        self.initSystemTray()

    def initUI(self):
        self.setWindowTitle('Chat and Animation')
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)


        # Set a fixed size for the window to act like a chatbox.
        chatboxWidth, chatboxHeight = 448, 600
        self.setFixedSize(chatboxWidth, chatboxHeight)

        screen = QApplication.primaryScreen().geometry()
        finalX = screen.width() - chatboxWidth - 10
        finalY = screen.height() - chatboxHeight - 50

        # Start position is off-screen at the bottom
        self.setGeometry(finalX, screen.height(), chatboxWidth, chatboxHeight)
        self.show()

        # Animate the window to scroll up into its final position
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(500)  # Animation duration in milliseconds
        self.animation.setStartValue(QRect(finalX, screen.height(), chatboxWidth, chatboxHeight))
        self.animation.setEndValue(QRect(finalX, finalY, chatboxWidth, chatboxHeight))
        self.animation.setEasingCurve(QEasingCurve.OutCubic)  # This easing curve will make the animation smooth
        self.animation.start()

        self.label.setFixedSize(200, 200)  # Adjust size as needed for images
        self.applyDefaultStyle()        
        # Settings button
        self.settings_button = QPushButton('Settings', self)
        self.settings_button.clicked.connect(self.openSettingsWindow)

        # Custom title bar
        self.title_bar = QWidget(self)
        self.title_bar.setStyleSheet("background-color: #333; color: #FFF;")
        self.title_label = QLabel('Suzy', self.title_bar)
        self.close_button = QPushButton('X', self.title_bar)
        self.close_button.clicked.connect(self.close)
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.close_button)

        # Layout for settings button
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(self.settings_button)
        settings_layout.addStretch()  # Add stretch to push the button to the left


        
        # Set default style if desired
        default_style = STYLES.get('default', {}).get('stylesheet', '')
        QApplication.instance().setStyleSheet(default_style)
    

        # Horizontal layout for animations and link display components
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.label)  # Add animation display
        top_layout.addWidget(self.link_display)  # Add link display area

        # Vertical layout for chat components
        chat_layout = QVBoxLayout()
        chat_layout.addWidget(self.chat_history)

        # Horizontal layout for input and buttons
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.mic_button)  # Add microphone button
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)

        chat_layout.addLayout(input_layout)
        # Add a button for creating a draft email
        self.createDraftEmailButton = QPushButton("Create Draft Email", self)
        self.createDraftEmailButton.clicked.connect(self.on_createDraftEmailButton_clicked)
        # Position the button appropriately
        self.createDraftEmailButton.move(10, 10)  # Example position
        # Main vertical layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.title_bar) 
        main_layout.addLayout(settings_layout)  # Add settings layout at the top
        main_layout.addLayout(top_layout)  # Add top layout with animations and links
        main_layout.addLayout(chat_layout)  # Add chat layout

        self.setLayout(main_layout)
        self.show()
        self.check_queue()
        self.title_bar.mouseMoveEvent = self.dragWindow
        self.applyDefaultStyle()
    def initSystemTray(self):
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(QIcon('./icons/chat.png'))  # Set your icon path

        # Tray icon menu
        self.trayMenu = QMenu(self)
        openAction = QAction('Open', self)
        openAction.triggered.connect(self.showNormal)
        exitAction = QAction('Exit', self)
        exitAction.triggered.connect(self.exitApplication)  # Connect to exitApplication method

        self.trayMenu.addAction(openAction)
        self.trayMenu.addAction(exitAction)
        self.trayIcon.setContextMenu(self.trayMenu)

        self.trayIcon.show()
        self.applyDefaultStyle()
        
    def on_createDraftEmailButton_clicked(self):
        # Start the worker thread
        self.worker = WorkerThread()
        self.worker.showDraftEmailSignal.connect(self.showDraftEmailWidget)
        self.worker.start()

    def showDraftEmailWidget(self, draft):
        # This method gets called when the signal is emitted
        self.draftEmailWidget = DraftEmailWidget(draft, self.handleDraftEmailResponse)
        self.draftEmailWidget.show()

    def handleDraftEmailResponse(self, response):
        # Handle the callback response here
        print(response)
     
        
    def closeEvent(self, event):
        event.ignore()  # Ignore the close event
        self.hide()  # Hide the window
        self.trayIcon.showMessage('Running', 'Application is running in the background.', QIcon('path/to/icon.png'))
    def exitApplication(self):
        # Ensure any cleanup or save state actions are performed here
        QCoreApplication.quit()  # Quit the application

    def showDraftEmailWidget(self, draft):
        # This method gets called when the signal is emitted
        self.draftEmailWidget = DraftEmailWidget(draft, self.handleDraftEmailResponse)
        self.draftEmailWidget.show()

    def handleDraftEmailResponse(self, response):
        # Handle the callback response here
        print(response)
        

    def handleLinkClicked(self, url):
        """Custom slot to handle clicked links."""
        if url.scheme() == 'file':
            # Handle local file URLs differently
            self.openLocalFile(url.toLocalFile())
        else:
            # Open web URLs in the default browser
            QDesktopServices.openUrl(url)

    def openLocalFile(self, file_path):
        """Open a local file using the appropriate method based on the OS."""
        if sys.platform == 'win32':
            os.startfile(file_path)
        elif sys.platform == 'darwin':  # macOS
            subprocess.run(['open', file_path])
        else:  # Linux and other Unix-like OS
            subprocess.run(['xdg-open', file_path])
    
    def applyDefaultStyle(self):
        config = load_config()  # Load your application's configuration
        default_style_name = config.get('Application', 'default_style', fallback='default')
        if default_style_name in STYLES:
            self.default_style = default_style_name  # Update self.default_style
            style_details = STYLES[default_style_name]
            self.applyStyle(style_details)
        else:
            print(f"Default style '{default_style_name}' not found. Applying default style.")


    def updateBackground(self):
        if hasattr(self, 'bg_movie') and self.bg_movie:
            pixmap = self.bg_movie.currentPixmap()
            brush = QBrush(pixmap)
            palette = self.palette()
            palette.setBrush(QPalette.Window, brush)
            self.setPalette(palette)


    def resizeEvent(self, event):
        if hasattr(self, 'video_widget'):
            self.video_widget.setGeometry(self.rect())
        super(LabelUpdater, self).resizeEvent(event)

    def applyStyle(self, style_details):
        # Apply the stylesheet
        style_sheet = style_details.get('stylesheet', '')
        QApplication.instance().setStyleSheet(style_sheet)
        
        # Handle background settings
        bg = style_details.get('background', {})

        # **Always stop any existing background animations**
        self.stopBackgroundAnimation()

        # Handle background color
        if 'color' in bg:
            color = bg['color']
            QApplication.instance().setPalette(QPalette(QColor(color)))
        else:
            # If no color is specified, reset the palette to default
            palette = QApplication.instance().palette()
            palette.setBrush(QPalette.Window, QBrush(Qt.NoBrush))
            QApplication.instance().setPalette(palette)

        # Handle background image
        if 'image' in bg:
            image_path = bg['image']
            if os.path.exists(image_path):
                if image_path.lower().endswith('.gif'):
                    # Use QMovie for GIFs
                    self.bg_movie = QMovie(image_path)
                    
                    # Configure the QMovie
                    self.bg_movie.setCacheMode(QMovie.CacheAll)
                    self.bg_movie.setSpeed(100)  # 100% speed
                    self.bg_movie.finished.connect(self.bg_movie.start)  # Loop infinitely
                    
                    # Connect the frameChanged signal
                    self.bg_movie.frameChanged.connect(self.updateBackground)
                    
                    # Start the QMovie
                    self.bg_movie.start()
                    
                elif image_path.lower().endswith(('.mp4', '.avi', '.mov')):
                    # Use QMediaPlayer and QVideoWidget for videos
                    self.video_widget = QVideoWidget(self)
                    self.video_widget.setGeometry(self.rect())
                    self.video_widget.lower()
                    self.video_widget.show()
        
                    self.player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
                    self.player.setVideoOutput(self.video_widget)
                    self.player.setMedia(QMediaContent(QUrl.fromLocalFile(image_path)))
                    self.player.play()
                    
                else:
                    # Use QPixmap for static images
                    pixmap = QPixmap(image_path)
                    mode = bg.get('mode', 'repeat')
                    if mode == 'fit':
                        pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    brush = QBrush(pixmap)
                    palette = QApplication.instance().palette()
                    palette.setBrush(QPalette.Window, brush)
                    QApplication.instance().setPalette(palette)
            else:
                print(f"Background image file does not exist: {image_path}")
        else:
            # No 'image' key, background is only color
            pass






    def stopBackgroundAnimation(self):
        # Stop and clean up any existing background animation
        if hasattr(self, 'bg_movie') and self.bg_movie:
            self.bg_movie.stop()
            self.bg_movie.deleteLater()
            del self.bg_movie

        if hasattr(self, 'player') and self.player:
            self.player.stop()
            self.player.deleteLater()
            del self.player

        if hasattr(self, 'video_widget') and self.video_widget:
            self.video_widget.hide()
            self.video_widget.deleteLater()
            del self.video_widget

        # Reset the palette to remove any background images
        palette = QApplication.instance().palette()
        palette.setBrush(QPalette.Window, QBrush(Qt.NoBrush))
        QApplication.instance().setPalette(palette)


    
    
    def openSettingsWindow(self):
        if self.settingsWindow is None or not self.settingsWindow.isVisible():
            self.settingsWindow = SettingsWindow()
            self.settingsWindow.styleChanged.connect(self.updateDefaultStyle)
            self.settingsWindow.styleChanged.connect(self.applyDefaultStyle)  # Connect the signal
            
            self.settingsWindow.show()
        else:
            self.settingsWindow.activateWindow()
    def updateDefaultStyle(self):
        config = load_config()
        new_default_style = config.get('Application', 'default_style', fallback='default')
        self.default_style = new_default_style  # Update self.default_style
        self.applyDefaultStyle()  # Re-apply the style if needed

        
    def dragWindow(self, event):
        # Check if left mouse button is pressed to drag the window
        if event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()
            event.accept()

    def mousePressEvent(self, event):
        # Record the initial position to calculate the movement
        self.dragPos = event.globalPos()
        
    def handle_mic_button(self):
        global listen_to_me
        if self.mic_button.isChecked():
            self.mic_button.setIcon(QIcon('./icons/mic_green.png'))  # Change to red icon
            listen_to_me = True
            mutedtalking = True
            print (listen_to_me)
        else:
            self.mic_button.setIcon(QIcon('./icons/mic_red.png'))  # Change back to green icon
            listen_to_me = False
            mutedtalking = False
            print (listen_to_me)
        # Enable clickable links in chat history
        self.chat_history.setOpenExternalLinks(False)  # If you want the links to open in a web browser
        

    def append_to_chat(self, message, file_link=None, display_name=None):
        """Append a given message to the chat history with optional link."""
        if file_link and display_name:
            # For local file links, prepend 'file://' to the file path
            if not file_link.startswith('http://') and not file_link.startswith('https://'):
                file_link = f'file:{pathname2url(file_link)}'
                print ('File Detected for link')
            
            # Close the anchor tag properly to ensure only the display name is a hyperlink
            message_with_link = f'{message} <a href="{file_link}">{display_name}</a>'
            self.link_display.append(message_with_link)
            
        else:
            self.chat_history.append(message)
               
            # Adjust the window size slightly to trigger a redraw
            # Force update of the chat and link display widgets
        self.chat_history.update()
        self.link_display.update()
        current_size = self.size()
            # Optionally, process all pending events to update UI immediately
        QApplication.processEvents()

        self.resize(current_size.width() + 1, current_size.height() + 1)
        QApplication.processEvents()  # Process events to apply resize
        self.resize(current_size.width(), current_size.height())
 
        # Force update of the chat and link display widgets
        self.chat_history.update()
        self.link_display.update()

        # Optionally, process all pending events to update UI immediately
        QApplication.processEvents()

        
    
    def handle_send_button(self):
        chatbox_text = self.message_input.toPlainText()
        # Add the text to chat history and clear the input area
        
        self.chat_history.append(f"You: {chatbox_text}")
        threading.Thread(target=process_chat_prompt, args=(chatbox_text,), daemon=True).start()
        threading.Thread(target=play_sound_effect, args=(Send_Message,), daemon=True).start()
        self.message_input.clear()

    def handle_link_clicked(self, url):
        """Handle clicked links in the chat history."""
        
        if url.scheme() == 'http' or url.scheme() == 'https':
            # Open web URLs in the default browser
            webbrowser.open(url.toString())
            print ('link Detected')
        elif url.scheme() == 'file':
            print ('File Detected')
            # Open local files based on the operating system
            file_path = url.toLocalFile()
            if sys.platform == 'win32':
                os.startfile(file_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', file_path])
            else:  # Linux and other Unix-like OS
                subprocess.run(['xdg-open', file_path])
        else:
            print(f"Unsupported URL scheme: {url.scheme()}")

    def check_queue(self):
        try:
            while True:
                anim = animation_queue.get_nowait()
                base_path = f"Animations/{self.default_style}/" + anim[1:-1]  # Use self.default_style
                possible_extensions = ['.png', '.gif', '.jpg', '.webp']

                image_path = None

                # Try to find the file with any of the possible extensions
                for ext in possible_extensions:
                    test_path = base_path + ext
                    if os.path.exists(test_path):
                        image_path = test_path
                        break  # Exit the loop once the file is found

                if image_path:
                    print(f"Attempting to load animation from: {image_path}")
                    if image_path.lower().endswith('.gif'):
                        # Use QMovie for GIFs
                        if self.movie:
                            self.movie.stop()
                        self.movie = QMovie(image_path)
                        self.label.setMovie(self.movie)
                        self.movie.start()
                    else:
                        # Use QPixmap for static images
                        if self.movie:
                            self.movie.stop()
                            self.movie = None
                        pixmap = QPixmap(image_path)
                        scaled_pixmap = pixmap.scaled(
                            self.label.size(),
                            Qt.KeepAspectRatioByExpanding,
                            Qt.SmoothTransformation
                        )
                        self.label.setPixmap(scaled_pixmap)
                else:
                    # If the image file is not found, display the text
                    if self.movie:
                        self.movie.stop()
                        self.movie = None
                    self.label.setText(anim[1:-1])  # Fallback to text if image not found

                QApplication.processEvents()
        except queue.Empty:
            pass
        QTimer.singleShot(100, self.check_queue)







def speak_text_thread(text, label_updater=None, animations_with_counts=None):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'female' in voice.name.lower():  # This is a simplification; adjust the condition as needed
            engine.setProperty('voice', voice.id)
            break

    # Optionally, adjust the speech rate
    engine.setProperty('rate', 150)
    if mutedtalking:
        engine.say(text)
    
    # If animations or label updates are part of your functionality, start them in a separate thread
    if animations_with_counts:
        threading.Thread(target=lambda: display_animation(animations_with_counts)).start()

    engine.runAndWait()
# Preprocess the text to extract spoken text and animation cues with word counts
def preprocess_text(text):
    # Split the text by newlines and keep only the first line
    first_line = text.split('\n', 1)[0]
    
    text_without_commands = re.sub(r'@\w+.*$', '', first_line)
    animations = [(m.group(), m.start()) for m in re.finditer(r'<(\w+)>', text_without_commands)]

    word_counts = []
    last_pos = 0
    for anim, pos in animations:
        word_count = len(re.findall(r'\b\w+\b', text_without_commands[last_pos:pos]))
        word_counts.append((anim, word_count))
        last_pos = pos

    spoken_text = re.sub(r'<\w+>', '', text_without_commands).strip()
    return spoken_text, word_counts
# Example usage
text = "Hello, this is an example text spoken with a feminine voice."
speak_text_thread(text)
def process_response_and_speak(response, label_updater):
    spoken_text, animations_with_counts = preprocess_text(response)
    threading.Thread(target=lambda: speak_text_thread(spoken_text, label_updater, animations_with_counts)).start()

def testemaildraft(draft):
    label_updater.communicator.show_draft_email_signal.emit(draft)


def load_and_update_sound_effects(style_name):
    global Send_Message, Receive_Message, Program_Message, Settings_Click, Ambient_Music
    
    sound_effects_file = f'./sounds/{style_name}.json'
    if not os.path.exists(sound_effects_file):
        print(f"Sound effects config for {style_name} not found.")
        # Fallback to default paths or set them to empty
        Send_Message = "./sounds/default/UpdateFlashlightB.wav"
        Receive_Message = "./sounds/default/UpdateFlashlightA.wav"
        Program_Message = "./sounds/default/UpdateFlashlightC.wav"
        Settings_Click = "./sounds/default/UpdateFlashlightB.wav"
        Ambient_Music = "./sounds/default/UpdateFlashlightB.wav"
        return

    with open(sound_effects_file, 'r') as file:
        sound_effects_config = json.load(file)
    
    # Update global variables with paths from the config
    Send_Message = sound_effects_config.get("Send_Message", "./sounds/default/UpdateFlashlightB.wav")
    Receive_Message = sound_effects_config.get("Receive_Message", "./sounds/default/UpdateFlashlightA.wav")
    Program_Message = sound_effects_config.get("Program_Message", "./sounds/default/UpdateFlashlightC.wav")
    Settings_Click = sound_effects_config.get("Settings_Click", "./sounds/default/UpdateFlashlightB.wav")
    Ambient_Music = sound_effects_config.get("Ambient_Music", "./sounds/default/UpdateFlashlightB.wav")



def listen_for_wake_word(audio):
    global listening_for_wake_word, command_ready
    print("Listening for wake word...")
    with open("wake_detect.wav", "wb") as f:
        f.write(audio.get_wav_data())
    try:
        process_response_and_speak('test <Neutral>', label_updater)
        result = tiny_model.transcribe('wake_detect.wav')
        text_input = result['text']
        print(f"Detected text: {text_input}")

        if wake_word.lower() in text_input.lower().strip():
            
            print("Wake word detected. Please speak your question.")

            listening_for_wake_word = False
            command_ready = True
            print(command_ready)

    except Exception as e:
        print("Error in wake word detection:", e)

def prompt_openai(audio):
    global listening_for_wake_word, command_ready
    print("Please speak your command...")
    try:
        # Process the audio directly without opening the microphone again
        with open("prompt.wav", "wb") as f:
            f.write(audio.get_wav_data())
        process_prompt()
    except Exception as e:
        print("Error in recording command:", e)
        


def process_prompt():
    global listening_for_wake_word, thread_id, assistant_id, last_command_time, not_continuing_convo, person_name, command_ready
    print("Starting prompt processing...")
    current_time = datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")
    try:
        print("Transcribing audio...")
        result = base_model.transcribe('prompt.wav')
        prompt_text = result['text']
        print("Detected Prompt: ", prompt_text)
        # Check if prompt text is less than 5 words
        if len(prompt_text.split()) < 5:
            print("Prompt too short, listening again...")
            listening_for_wake_word = True
            command_ready = False
            return  # Exit the function early

        print("Creating message in the thread...")
        message = openai.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content= person_name + ': ' + prompt_text + ' #' + current_time
        )

        print("Running the assistant...")
        run = openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        print("Waiting for response...")
        time.sleep(20)  # Adjust as needed

        print("Retrieving response messages...")
        response_messages = openai.beta.threads.messages.list(thread_id=thread_id)

        print("Processing the latest response message...")
        for msg in response_messages.data[:]:
            if msg.role == "assistant":
                response_texts = [content.text.value for content in msg.content if hasattr(content, 'text')]
                response_text = ''.join(response_texts)
                print("Suzy's Response: ", response_texts)
                print("Suzy's Response: ", response_text)

                try:
                    response_texts = [content.text.value for content in msg.content if hasattr(content, 'text')]
                    response_text = ''.join(response_texts)
                    print("Suzy's Response: ", response_text)

                    print("Processing JSON response...")
                    # Strip markdown code block delimiters and newlines
                    json_str = response_text.replace("```json\n", "").replace("\n```", "").strip()
                    
                    # # Regular expression to remove extraneous commas
                    # json_str = re.sub(r',\s*}', '}', json_str)
                    # json_str = re.sub(r',\s*\]', ']', json_str)
                    # json_str = re.sub(r',\s*$', '', json_str, flags=re.MULTILINE)
                    # json_str = re.sub(r',\s*}', '}', json_str)
                    
                    # Print the JSON string before parsing (for debugging)
                    print("Formatted JSON String:", json_str)

                    json_data = json.loads(json_str)

                    file_name = "responses.json"
                    with open(file_name, 'r+') as f:
                        try:
                            existing_json = json.load(f)
                        except json.JSONDecodeError:  # Correct exception type
                            existing_json = []

                        existing_json.append(json_data)
                        f.seek(0)
                        json.dump(existing_json, f, indent=4)
                        f.truncate()

                    print(f"Response appended to {file_name}")
                    
                    # Extracting the "Response" from the JSON data
                    response_variable = json_data.get("Response", "")
                    print("Extracted Response: ", response_variable)
                    process_response_and_speak(response_variable, label_updater)
                    Program_Response = response_commands(response_variable)
                    
                    response1 = re.sub(r'<[^>]*>', '', response_variable)
                    
                    response2 = re.sub(r'@.*', '', response1)
                    
                    # Assuming 'label_updater' is your instance of LabelUpdater
                    label_updater.append_to_chat(f"Suzy:{response2}")
                    
                    if Program_Response:
                        process_results(Program_Response)  # Recursive call if new commands are found                    
                    
                except json.JSONDecodeError:  # Correct exception type
                    print("Error: Extracted string is not in valid JSON format")
                last_command_time = time.time()
                not_continuing_convo = True
                listening_for_wake_word = False
                command_ready = True
                break  # Exit after processing the latest message

    except Exception as e:
        print("Prompt error for Process_prompt: ", e)
        listening_for_wake_word = True  # Reset state

def process_chat_prompt(chat_message):
    global listening_for_wake_word, thread_id, assistant_id, last_command_time, not_continuing_convo, person_name, command_ready
    print("Starting prompt processing...")
    current_time = datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")
    try:
        print("Transcribing audio...")
        result = chat_message
        prompt_text = result
        print("Detected Prompt: ", prompt_text)
        print("Creating message in the thread...")
        message = openai.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content= person_name + ': ' + prompt_text + ' #' + current_time
        )

        print("Running the assistant...")
        run = openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        print("Waiting for response...")
        time.sleep(40)  # Adjust as needed

        print("Retrieving response messages...")
        response_messages = openai.beta.threads.messages.list(thread_id=thread_id)

        print("Processing the latest response message...")
        for msg in response_messages.data[:]:
            if msg.role == "assistant":
                response_texts = [content.text.value for content in msg.content if hasattr(content, 'text')]
                response_text = ''.join(response_texts)
                print("Suzy's Response: ", response_texts)
                print("Suzy's Response: ", response_text)

                try:
                    response_texts = [content.text.value for content in msg.content if hasattr(content, 'text')]
                    response_text = ''.join(response_texts)
                    print("Suzy's Response: ", response_text)

                    print("Processing JSON response...")
                    # Strip markdown code block delimiters and newlines
                    json_str = response_text.replace("```json\n", "").replace("\n```", "").strip()
                    
                    # # Regular expression to remove extraneous commas
                    # json_str = re.sub(r',\s*}', '}', json_str)
                    # json_str = re.sub(r',\s*\]', ']', json_str)
                    # json_str = re.sub(r',\s*$', '', json_str, flags=re.MULTILINE)
                    # json_str = re.sub(r',\s*}', '}', json_str)
                    
                    # Print the JSON string before parsing (for debugging)
                    print("Formatted JSON String:", json_str)

                    json_data = json.loads(json_str)

                    file_name = "responses.json"
                    with open(file_name, 'r+') as f:
                        try:
                            existing_json = json.load(f)
                        except json.JSONDecodeError:  # Correct exception type
                            existing_json = []

                        existing_json.append(json_data)
                        f.seek(0)
                        json.dump(existing_json, f, indent=4)
                        f.truncate()

                    print(f"Response appended to {file_name}")
                    
                    # Extracting the "Response" from the JSON data
                    response_variable = json_data.get("Response", "")
                    print("Extracted Response: ", response_variable)
                    process_response_and_speak(response_variable, label_updater)
                    Program_Response = response_commands(response_variable)
                    
                    
                    response1 = re.sub(r'<[^>]*>', '', response_variable)
                    
                    response2 = re.sub(r'@.*', '', response1)
                    
                    # Assuming 'label_updater' is your instance of LabelUpdater
                    label_updater.append_to_chat(f"Suzy:{response2}")
                    threading.Thread(target=play_sound_effect, args=(Receive_Message,), daemon=True).start()

                    if Program_Response:
                        process_results(Program_Response)  # Recursive call if new commands are found   
                    re.sub(r'<.*?>', '', response_variable)
                    

                except json.JSONDecodeError:  # Correct exception type
                    print("Error: Extracted string is not in valid JSON format")
                last_command_time = time.time()
                not_continuing_convo = True
                listening_for_wake_word = False
                command_ready = True
                break  # Exit after processing the latest message

    except Exception as e:
        print("Prompt error for Process_prompt: ", e)
        listening_for_wake_word = True  # Reset state


def process_wake_word(audio):
    global listening_for_wake_word, command_ready
    print("Processing wake word...")
    try:
        # Convert audio to a numpy array of float32
        audio_data = np.frombuffer(audio.get_wav_data(convert_rate=16000, convert_width=2), np.int16)
        audio_data = audio_data.astype(np.float32)

        # Normalize the audio data
        audio_data /= np.iinfo(np.int16).max

        result = tiny_model.transcribe(audio_data)
        text_input = result['text']
        print(f"Detected text: {text_input}")
        
        if wake_word.lower() in text_input.lower().strip():
            
            print("Wake word detected. Please speak your question.")
            listening_for_wake_word = False
            command_ready = True
    except Exception as e:
        print("Error in wake word processing:", e)

def callback(recognizer, audio):
    print("Audio captured")
    global last_command_time, listening_for_wake_word, command_ready, listen_to_me
    
    # Check if we should listen to the audio
    if not listen_to_me:
        return  # Do nothing if listen_to_me is False    
    
    if listening_for_wake_word:
        process_wake_word(audio)
    elif command_ready:
        print("Please speak your command...")
        try:
            # Process the captured command
            prompt_openai(audio)
            #command_ready = False
            #listening_for_wake_word = True
            last_command_time = time.time()  # Reset the timer after processing a command
        except Exception as e:
            print("Error in processing command:", e)
            



r.dynamic_energy_threshold = False


def start_listening():
    global last_command_time, listening_for_wake_word, command_ready, not_continuing_convo, source
    print('Say', wake_word, 'to wake me up. ')
    
    # Open the audio source in a with statement
    with source as s:
        r.adjust_for_ambient_noise(s, duration=10)  # Adjust for ambient noise
        r.energy_threshold = 300  # or adjust based on testing

    # Now start the background listening
    r.listen_in_background(source, callback)
    while True:
        time.sleep(1)
        # Check if more than 50 seconds have passed since the last command
        if not_continuing_convo:
            if time.time() - last_command_time > 50:
                listening_for_wake_word = True
                command_ready = False
                not_continuing_convo = False
                print('No longer talking together')



def response_commands(response):
    # Regular expression to find commands and their arguments
    command_regex = r"@(\w+)([^\@]*)"
    commands_with_args = re.findall(command_regex, response)
    results = []  # List to store results of all commands
    database = load_database()
    
    # Check if no commands are found
    if not commands_with_args:
        print("No commands found in response.")
        return

    # Process each command with its argument
    for command, argument in commands_with_args:
        argument = argument.strip()  # Remove leading and trailing whitespace

        if command == "Math":
            math_result = math(argument)
            print(f"Math command result: {math_result}")
            results.append(f"Math command result: {math_result}")

        elif command == "ChangePersonName":
            name_change_result = ChangePersonName(argument)
            results.append(name_change_result)

        elif command == "Calendar":
            calendar_result = calendar(argument)
            print(f"Calendar command result: {calendar_result}")
            results.append(f"Calendar command result: {calendar_result}")
            
        elif command == "SelfMessage":
            self_message_result = self_message(argument)
            print(f"Self Message command result: {self_message_result}")
            results.append(f"Self Message command result: {self_message_result}")              

        elif command == "FileFolderSearch":
            search_query = argument
            print(f"Processing FileFolderSearch command with query: {search_query}")
            search_results = FileFolderSearch(search_query)
            results.append(search_results)  
        
        elif command == "CreateLink":
            print("Processing CreateLink command...")
            # Split the argument to extract URL and display name
            parts = argument.split('"')
            if len(parts) >= 3 and parts[0].strip() and parts[1].strip():
                web_url = parts[0].strip()
                display_name = parts[1].strip()
                label_updater.append_to_chat("Link:", file_link=web_url, display_name=display_name)
                results.append(f"Link to Website Created: {display_name}")
            else:
                message = 'To create a link, please perform the command as follows: @CreateLink -Website here- "display name here". Example: @CreateLink https://google.com "Google"'
                
                results.append(message)     
        
        elif command == "DraftEmail":
            draftemail = argument
            label_updater.append_to_chat(f"Email Draft:{draftemail}")
            # Copy draftemail to clipboardthreading.Thread(target=testemaildraft, daemon=True).start()
            #clipboard = QApplication.clipboard()
            #clipboard.setText(draftemail)
            testemaildraft(draftemail)
            # UserResult = showDraftEmailWidget(draftemail)
            results.append(f"Email being reviewed.")           
        
        elif command == "Weather":
            print("Processing Weather command...")
            try:
                WeatherComeback = process_weather_command(argument)  # Assuming you have the API key defined elsewhere
                results.append(f"{WeatherComeback}")
            except Exception as e:
                results.append(f"To use Weather command Preform command like following '@Weather city state' Example: '@Weather Jackson Tennnesse' Failed to get weather data: {e}")
            
        elif command == "Translate":
            print("Processing Translate command...")
            results.append(f"Translate command not implimented yet")  
            
        elif command == "InformationDatabase":
            print("Processing Information Database command...")
            # Extract the subcommand and its arguments
            # Load the database
            database = load_database()
            subcommand_regex = r"(\w+)\s*(.*)"
            match = re.match(subcommand_regex, argument)
            if match:
                subcommand, subargument = match.groups()
                result = process_information_database(subcommand, subargument, database)
                results.append(result)
            else:
                results.append("Invalid InformationDatabase command format.")
            
        elif command == "UserMemory":
            print("Processing User Memory command...")
            results.append(f"UserMemory command not implimented yet") 
            
        elif command == "InternetSearch":
            print("Processing Internet Search command...")
            # Placeholder for actual search functionality
            search_results = internet_search(argument)
            results.append(search_results)
            
        elif command == "SmartHome":
            print("Processing Smart Home command...")
            results.append(f"SmartHome command not implimented yet")  
            
        elif command == "CurrentKnowledge":
            print("Processing Current Knowledge command...")
            results.append(f"CurrentKnowledge command not implimented yet")  

        else:
            print(f"Unrecognized command: {command}, with argument: {argument}")
            results.append(f"Unrecognized command: {command}, with argument: {argument}")

    return ' and '.join(results)  # Join all results into a single string
DATABASE_FILE_PATH = 'information_database.json'

# Load the information database from the JSON file
def load_database(file_path=DATABASE_FILE_PATH):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            json.dump([], file)
    with open(file_path, 'r') as file:
        return json.load(file)

# Save the information database to the JSON file
def save_database(data, file_path=DATABASE_FILE_PATH):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# Search the information database
def search_database(query, database):
    query_words = query.lower().split()
    relevance_scores = []

    for i, entry in enumerate(database):
        entry_lower = entry.lower()
        match_count = sum(entry_lower.count(word) for word in query_words)
        if match_count > 0:
            relevance_scores.append((i, entry, match_count))
    
    # Sort the entries by the number of matching words (highest first)
    relevance_scores.sort(key=lambda x: x[2], reverse=True)

    # If no entries are found, return a message
    if not relevance_scores:
        return "No entries have been made or search criteria not met. Use multiple words."    
    
    # If fewer than 10 entries are found, return all matching entries
    if len(relevance_scores) < 10:
        return [(i, entry) for i, entry, _ in relevance_scores]
    # Otherwise, return the top 10 entries
    return [(i, entry) for i, entry, _ in relevance_scores[:10]]

# Add to the information database
def add_to_database(entry, database):
    database.append(entry)
    save_database(database)

# Remove from the information database
def remove_from_database(entry_id, database):
    if 0 <= entry_id < len(database):
        del database[entry_id]
        save_database(database)
        return True
    return False

# Modify an entry in the information database
def modify_database(entry_id, new_entry, database):
    if 0 <= entry_id < len(database):
        database[entry_id] = new_entry
        save_database(database)
        return True
    return False

# Process the InformationDatabase command
def process_information_database(command, argument, database):
    if command == "search":
        if not argument:
            return "To utilize the search command in InformationDatabase, you must use it as follows: *@InformationDatabase search \"Description in quotes\"*"
        else:
            results = search_database(argument, database)
            if isinstance(results, str):  # Check if the result is a message
                return results
            return "\n".join([f"{i}: {entry}" for i, entry in results])
    
    
    elif command == "add":
        if not argument:
            return "To utilize the add command in InformationDatabase, you must use it as follows: *@InformationDatabase add \"Information to be stored.\"* This will append that info to the last of the database."
        else:
            add_to_database(argument, database)
            return "Entry added to the database."
    
    elif command == "remove":
        if not argument:
            return "To utilize the remove command in InformationDatabase, you must use it as follows: *@InformationDatabase remove \"the entry ID\"* if you are uncertain of which item to remove ask the human. More than often it's probably the item you both were just discussing."
        else:
            try:
                entry_id = int(argument)
                if remove_from_database(entry_id, database):
                    return f"Entry with ID {entry_id} removed from the database."
                else:
                    return f"Error: No entry found with ID {entry_id}."
            except ValueError:
                return "Error: The entry ID must be an integer."
    
    elif command == "modify":
        parts = argument.split(maxsplit=1)
        if len(parts) < 2:
            return "To utilize the modify command in InformationDatabase, you must use it as follows: *@InformationDatabase modify ID \"Replacement text\"*"
        else:
            try:
                entry_id = int(parts[0])
                new_entry = parts[1].strip('"')
                if modify_database(entry_id, new_entry, database):
                    return f"Entry with ID {entry_id} modified."
                else:
                    return f"Error: No entry found with ID {entry_id}."
            except ValueError:
                return "Error: The entry ID must be an integer."
    
    return "Unknown command. Please use search, add, remove, or modify when using the InromationDatabase command."

Weather_api_key = get_setting(config, 'Application', 'Weather_API_KEY', 'Ask for my KEY')
def fetch_weather(city, state):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    query = f"{city},{state}" if state else city
    params = {
        'q': query,
        'appid': Weather_api_key,
        'units': 'metric'
    }
    request_url = f"{base_url}?{urlencode(params)}"
    response = requests.get(request_url)
    if response.status_code == 200:
        data = response.json()
        # Assuming you want current weather. For forecasts, you'd use a different API endpoint and process the date
        weather_description = data['weather'][0]['description']
        temperature = data['main']['temp']
        return f"Weather in {city}: {weather_description}, Temp: {temperature}°C"
    else:
        return "Weather information could not be retrieved."


def process_weather_command(command):
    parts = command.split(", ")
    if len(parts) < 1:
        return "Invalid format. Please use 'City, State, Date' format."
    
    city = parts[0]
    state = parts[1] if len(parts) > 1 else None
    date = parts[2] if len(parts) > 2 else None  # You might not use date for current weather APIs
    
    weather_info = fetch_weather(city, state)
    return weather_info


class DraftEmailWidget(QWidget):
    def __init__(self, draft, callback):
        super().__init__()
        self.callback = callback
        self.mousePressPos = None
        self.mouseMovePos = None
        self.initUI(draft)



    def initUI(self, draft):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # Widget size and positioning
        widgetWidth = 300
        widgetHeight = 100
        screenSize = QDesktopWidget().screenGeometry()
        cursorPos = QCursor.pos()
        x = min(cursorPos.x(), screenSize.width() - widgetWidth)
        y = min(cursorPos.y(), screenSize.height() - widgetHeight)
        self.setGeometry(x, y, widgetWidth, widgetHeight)

        # Main layout
        mainLayout = QHBoxLayout(self)

        # Draggable bar
        self.draggableBar = QLabel()
        self.draggableBar.setFixedSize(10, widgetHeight)
        self.draggableBar.setStyleSheet("background-color: black;")
        self.draggableBar.setText("\n\n\n")  # Simple visual indicator
        mainLayout.addWidget(self.draggableBar)

        # Content layout
        contentLayout = QVBoxLayout()
        self.textEdit = QTextEdit()
        self.textEdit.setText(draft)
        contentLayout.addWidget(self.textEdit)

        # Button layout
        buttonLayout = QHBoxLayout()
        self.nahButton = QPushButton("Nah try again")
        self.nahButton.clicked.connect(lambda: self.onNahClicked(draft))
        buttonLayout.addWidget(self.nahButton)

        self.copyButton = QPushButton("Copy to clipboard")
        self.copyButton.clicked.connect(self.onCopyClicked)
        buttonLayout.addWidget(self.copyButton)

        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.onCancelClicked)
        buttonLayout.addWidget(self.cancelButton)

        # Integrating layouts
        contentLayout.addLayout(buttonLayout)
        mainLayout.addLayout(contentLayout)
        self.setLayout(mainLayout)
        self.show()

    def onNahClicked(self):
        self.callback("Try to draft the email differently")
        threading.Thread(target=process_results, args=(f"Try to draft the email differently. Review previous request and judge your email on the request.",), daemon=True).start()
        self.close()

    def onCopyClicked(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.textEdit.toPlainText())
        threading.Thread(target=process_results, args=(f"{person_name} Copied the Draft Email",), daemon=True).start()        

        self.close()

    def onCancelClicked(self):
        self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.oldPos = None


                
def showDraftEmailWidget(draft):
    def callback(result):
        print(result)  # or handle the result in any other way

    global draftWidget  # Keep a reference to avoid garbage collection
    draftWidget = DraftEmailWidget(draft, callback)


def math(argument):
    print(f"Debug: Original argument - '{argument}'")  # Debug print

    # Split the argument into words
    words = argument.split()
    print(f"Debug: Split words - {words}")  # Debug print

    # Check if there are any words in the argument
    if not words:
        return "No operation specified for Math command."

    # Check the first word to determine the operation
    if words[0] == "simple":
        expression = ' '.join(words[1:])
        print(f"Debug: Evaluating expression - '{expression}'")  # Debug print
        return evaluate_expression(expression)
    elif words[0] == "solve_for_x":
        equation_str = ' '.join(words[1:])
        print(f"Debug: Solving for x in - '{equation_str}'")  # Debug print
        return solve_for_x(equation_str)
    else:
        return "The math command should use either 'solve_for_x' for problems like 'x + 1 = 2' or 'simple' for problems like '1 + 2 ** 3'.\nExample: @Math simple 5 / 2"
        print(f"The math command should use either 'solve_for_x' for problems like 'x + 1 = 2' or 'simple' for problems like '1 + 2 ** 3'.\nExample: @Math simple 5 / 2")  # Debug print


def evaluate_expression(expression):
    try:
        # Parse the expression safely
        expr = sp.sympify(expression)
        # Evaluate the expression
        result = expr.evalf()
        return result
    except Exception as e:
        return f"Error: {e}"


def format_equation(equation_str):
    # Replace '^' with '**' for exponentiation
    formatted_str = equation_str.replace('^', '**')

    # Insert multiplication where necessary
    # Look for patterns like "2x" or "(3+2)x" and insert '*' before 'x'
    formatted_str = re.sub(r'(?<=\d)x', r'*x', formatted_str)  # after a number
    formatted_str = re.sub(r'(?<=\))x', r'*x', formatted_str)  # after a closing parenthesis

    return formatted_str

def solve_for_x(equation_str):
    try:
        x = sp.symbols('x')
        # Define allowed symbols
        allowed_symbols = {'x': x}
        # Parse expressions with allowed symbols only
        lhs_str, rhs_str = equation_str.split('=')
        lhs = sp.sympify(lhs_str, locals=allowed_symbols)
        rhs = sp.sympify(rhs_str, locals=allowed_symbols)
        equation = sp.Eq(lhs, rhs)
        solutions = sp.solve(equation, x)
        return solutions
    except sp.SympifyError:
        return "Error: Equation could not be interpreted."
    except Exception as e:
        return f"Error solving equation: {e}"

def ChangePersonName(argument):
    global person_name
    person_name = argument  # Update the global variable
    
    config = load_config()  # Load the current config
    if 'Application' not in config:
        config.add_section('Application')
    config.set('Application', 'person_name', person_name)  # Update the config with the new person name
    save_config(config)  # Save the updated config back to file
    
    return f"Person name changed to {person_name}."  # Return a confirmation message





def process_results(Program_Response):
    global listening_for_wake_word, thread_id, assistant_id, command_ready, not_continuing_convo
    print("Starting prompt processing...")
    label_updater.append_to_chat(f"Program:{Program_Response}")
    threading.Thread(target=play_sound_effect, args=(Program_Message,), daemon=True).start()

    current_time = datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")
    
    try:
        print("Creating message in the thread...")
        message = openai.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content='Program:' + Program_Response + ' #' + current_time
        )

        print("Running the assistant...")
        run = openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        print("Waiting for response...")
        time.sleep(30)  # Adjust as needed

        print("Retrieving response messages...")
        response_messages = openai.beta.threads.messages.list(thread_id=thread_id)

        print("Processing the latest response message...")
        for msg in response_messages.data[:]:
            if msg.role == "assistant":
                response_texts = [content.text.value for content in msg.content if hasattr(content, 'text')]
                response_text = ''.join(response_texts)
                print("Suzy's Response: ", response_text)

                try:
                    print("Processing JSON response...")
                    # Strip markdown code block delimiters and newlines
                    json_str = response_text.replace("```json\n", "").replace("\n```", "").strip()
                    
                    # Regular expression to remove extraneous commas
                    # json_str = re.sub(r',\s*}', '}', json_str)
                    # json_str = re.sub(r',\s*\]', ']', json_str)
                    # json_str = re.sub(r',\s*$', '', json_str, flags=re.MULTILINE)
                    # json_str = re.sub(r',\s*}', '}', json_str)
                    print("Formatted JSON String:", json_str)
                    json_data = json.loads(json_str)

                    file_name = "responses.json"
                    with open(file_name, 'r+') as f:
                        try:
                            existing_json = json.load(f)
                        except json.JSONDecodeError:  # Correct exception type
                            existing_json = []

                        existing_json.append(json_data)
                        f.seek(0)
                        json.dump(existing_json, f, indent=4)
                        f.truncate()

                    print(f"Response appended to {file_name}")
                    
                    # Extracting the "Response" from the JSON data
                    response_variable = json_data.get("Response", "")
                    print("Extracted Response: ", response_variable)
                    process_response_and_speak(response_variable, label_updater)
                    Program_Response = response_commands(response_variable)
                    
                    
                    
                    response1 = re.sub(r'<[^>]*>', '', response_variable)
                    
                    response2 = re.sub(r'@.*', '', response1)
                    
                    # Assuming 'label_updater' is your instance of LabelUpdater
                    label_updater.append_to_chat(f"Suzy:{response2}")
                    threading.Thread(target=play_sound_effect, args=(Receive_Message,), daemon=True).start()

                    if Program_Response:
                        process_results(Program_Response)  # Recursive call if new commands are found                    
                    
                except json.JSONDecodeError:  # Correct exception type
                    print("Error: Extracted string is not in valid JSON format")
                listening_for_wake_word = False
                command_ready = True
                not_continuing_convo = True
                break  # Exit after processing the latest message
    except Exception as e:
        print("Error processing results: ", e)
        listening_for_wake_word = True  # Reset state


# File to store events
events_file = Path("events.json")

# Initialize the events file if it does not exist
if not events_file.exists():
    events_file.write_text("[]")

def save_events(events):
    with open(events_file, 'w') as file:
        json.dump(events, file)

def load_events():
    with open(events_file, 'r') as file:
        return json.load(file)

def add_event(args):
    if len(args) < 2:
        return "Insufficient arguments. Usage: @calendar add YYYY-MM-DDTHH:MM:SS Event description"

    date_time = args[0]
    event_info = ' '.join(args[1:])  # Join the rest of the arguments as event description

    # Ensure date_time is in ISO 8601 format
    try:
        datetime.fromisoformat(date_time)
    except ValueError:
        return "Invalid format. Please use following the example: @calendar add 2020-12-13T13:14:10 April_has_an_appointment."

    events = load_events()
    events.append({'date_time': date_time, 'event_info': event_info, 'Alerted': False})
    save_events(events)
    return "Event added successfully."


    
    
def remove_event(date_time):
    try:
        # Validate the date_time format
        datetime.fromisoformat(date_time)

        events = load_events()
        original_count = len(events)
        # Remove events that match the specified date and time
        events = [event for event in events if event['date_time'] != date_time]
        save_events(events)

        removed_count = original_count - len(events)
        if removed_count > 0:
            return f"Successfully removed {removed_count} event(s)."
        else:
            return "No matching events found to remove. Please ensure that you are using @calendar remove YYYY-MM-DDTHH:MM:SS"

    except ValueError:
        return "Invalid date-time format. Please ensure that you are using @calendar remove YYYY-MM-DDTHH:MM:SS"



def upcoming(days):
    try:
        # Convert days to an integer
        days = int(days)

        today = datetime.now()
        future = today + timedelta(days=days)
        events = load_events()
        upcoming_events = [event for event in events if today <= datetime.fromisoformat(event['date_time']) <= future]

        # Format the list of events into a readable string
        formatted_events = '\n'.join([f"{event['date_time']}: {event['event_info']}" for event in upcoming_events])
        return formatted_events if formatted_events else "No upcoming events in the next {} days.".format(days)

    except ValueError:
        # This could occur if 'days' is not a number or if a date_time is not in the correct format
        return "Invalid input. Please use a number for days. Example: @Calendar upcoming 4"

       

def calendar(arguments):
    try:
        args = arguments.split()
        if not args:
            return "No command provided. Please use Add, Remove, or Upcoming."

        command = args.pop(0)  # Extract and remove the first word as command

        if command == 'Add':
            return add_event(args)  # Pass the remaining arguments as a list
        elif command == 'Remove':
            # Only consider the first argument for the Remove command
            return remove_event(args[0]) if args else "No argument provided for Remove."
        elif command == 'Upcoming':
            return upcoming(*args)
        else:
            return "Invalid command. Please use Add, Remove, or Upcoming. Example: @calendar Remove"
    except Exception as e:
        return f"An error occurred: {e}"


def index_directory(path):
    index = {}
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            type, _ = mimetypes.guess_type(file_path)
            index[file_path] = type or 'unknown'
    return index

def save_index(index, filename):
    with open(filename, 'w') as f:
        json.dump(index, f)

def load_index(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Create the file with default content if it does not exist
        with open(filename, 'w') as f:
            json.dump({}, f)  # Assuming you want an empty dictionary as default
        return {}


def FileFolderSearch(arguments):
    try:
        # Split the arguments string into category and keywords
        parts = arguments.split(':')
        if len(parts) != 2:
            print("Error: Invalid format")
            return "Invalid format. Expected 'category: keyword1 keyword2 ...' Example 'text: form quality dock audit'"

        category = parts[0].strip()
        keywords = parts[1].split()
        if len(keywords) < 1:
            print("Error: Not enough keywords")
            return "At least two keywords are required."

        # A list to hold tuples of (path, number of matches)
        results = []

        # Check if index is defined
        if 'index' not in globals():
            print("Error: 'index' is not defined")
            return "Error: 'index' is not defined in the current scope."

        for path, mime_type in index.items():
            if category in mime_type:
                # Normalize the path to improve matching accuracy
                normalized_path = path.replace("\\", "/").lower().replace("_", " ").replace("-", " ")
                matches = sum(keyword.lower() in normalized_path for keyword in keywords)
                # Append the path and the number of matches as a tuple
                results.append((path, matches))

        # Sort the results by the number of matches in descending order
        results.sort(key=lambda x: x[1], reverse=True)

        # Check if label_updater is defined
        if 'label_updater' not in globals():
            print("Error: 'label_updater' is not defined")
            return "Error: 'label_updater' is not defined in the current scope."

        # Append results to chat and handle no results found
        if not results:
            label_updater.append_to_chat("No results found")
            return "No results found, perhaps include alternative words. This includes shortened versions of the words or words of the same category. Use a minimum of 10 words in your search."

        # Append each result to chat with a clickable link
        for result, match_count in results[:10]:  # Limit to the top 10 results
            display_name = os.path.basename(result)  # Extract file name from path
            label_updater.append_to_chat("Found:", file_link=result, display_name=display_name)

        print(f"send return")
        # Return the top 10 file names with a specific message
        top_file_names = [os.path.basename(result[0]) for result in results[:10]]
        return "Offer the most likely option from these: " + ", ".join(top_file_names)

    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Error: {e}. To use FileFolderSearch, use the format: @FileFolderSearch file_category: keywords. Example: @FileFolderSearch text/plain: emotions list Suzy"

index = load_index('file_index.json')

def weekly_indexing_task():
    print("Starting weekly indexing...")
    index = index_directory(index_directory_path)
    save_index(index, 'file_index.json')
    
    print("Indexing completed.")
    while True:
        time.sleep(60)
        schedule.run_pending()
    

def run_calendar():
    
    while True:
        now = datetime.now()
        events = load_events()
        updated_events = False
        for event in events:
            event_datetime = datetime.fromisoformat(event['date_time'])
            if now >= event_datetime and not event.get('Alerted', False):
                print(f"Event alert: {event['event_info']}")
                
                event['Alerted'] = True
                updated_events = True
                # Perform the task related to the event
                process_results(f"calendar Alert:{event['event_info']}")

        if updated_events:
            save_events(events)
        time.sleep(60)  # Check every minute
        schedule.run_pending()
        

schedule.every().week.do(weekly_indexing_task)

# Queue to hold self messages
self_messages = queue.Queue()

def add_self_message(delay, message):
    delivery_time = datetime.now() + timedelta(seconds=delay)
    self_messages.put((delivery_time, message))

def process_self_messages():
    while True:
        now = datetime.now()
        while not self_messages.empty():
            delivery_time, message = self_messages.queue[0]  # Peek at the first message
            if now >= delivery_time:
                self_messages.get()  # Remove the message from the queue
                process_results(f"Message from past me: {message}")
            else:
                break
        time.sleep(60)  # Check every minute

def self_message(arguments):
    args = arguments.split(' ', 1)
    if len(args) != 2:
        return "Invalid format. Use: @selfmessage <time in seconds> 'Your message'"
    try:
        delay = int(args[0])
        message = args[1]
        add_self_message(delay, message)
        return f"Message scheduled to be sent in {delay} seconds."
    except ValueError:
        return "Invalid time format. Please provide the time in seconds."

def play_sound_effect(sound_filename):
    if soundON:
        sound_file = f'{sound_filename}'
        if os.path.exists(sound_file):
            try:
                # Load the sound file
                sound_effect = pygame.mixer.Sound(sound_file)
                # Play the sound effect
                sound_effect.play()
                print(f"Playing sound effect: {sound_filename}")
            except Exception as e:
                print(f"Error playing sound effect: {e}")
        else:
            print(f"Sound effect file not found: {sound_filename}")
    else:
        print("Sound is turned off. Cannot play sound effect.")


response_commands("@Math simple 15+27")
print(solve_for_x("x + 2 = 4"))  # Should output the solution for x
load_and_update_sound_effects(default_style)



class AppRunner(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.app = QApplication(sys.argv)
        self.label_updater = LabelUpdater()

    def run(self):
        start_listening()
        sys.exit(self.app.exec_())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    label_updater = LabelUpdater()
    #showDraftEmailWidget("draftemail")
    # Define the start-up animation
    startup_animation = "<Neutral>"  # Replace <Smiling> with your desired animation

    # Add the start-up animation to the queue
    animation_queue.put(startup_animation)
    threading.Thread(target=start_listening, daemon=True).start()  # Run speech recognition in a separate thread
    
    threading.Thread(target=run_calendar, daemon=True).start()
    threading.Thread(target=process_self_messages, daemon=True).start()  # Process self messages in a separate thread
    
    # Testing with a file link (adjust the path to an existing file on your system)
    #file_path = os.path.abspath("./test.txt")  # Replace with an actual file path
    #label_updater.append_to_chat("Check this file:", file_link=file_path, display_name="Local File")

    # Testing with a web link
    #web_url = "http://www.example.com"
    #label_updater.append_to_chat("Visit this website:", file_link=web_url, display_name="Example Site")

    
    sys.exit(app.exec_())

