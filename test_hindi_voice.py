import asyncio
import edge_tts
import pygame
import tempfile
import os
import time

def speak_hindi(message):
    async def generate_audio(file_path):
        communicate = edge_tts.Communicate(
            message,
            "hi-IN-MadhurNeural"
        )
        await communicate.save(file_path)

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temporary_file:
        audio_file = temporary_file.name

    try:
        asyncio.run(generate_audio(audio_file))

        if not pygame.mixer.get_init():
            pygame.mixer.init()

        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        pygame.mixer.music.unload()

    finally:
        if os.path.exists(audio_file):
            os.remove(audio_file)