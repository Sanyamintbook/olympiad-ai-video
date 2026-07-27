import os
import urllib.request
import io
import soundfile as sf
from loguru import logger
from app.infrastructure.audio.base import TTSProvider
from app.core.exceptions import VoiceGenerationException

class KokoroTTSProvider(TTSProvider):
    """
    Kokoro v1.0 ONNX TTS implementation for local, human-like voice synthesis.
    """
    def __init__(self, voice: str = "af_heart") -> None:
        self.voice = voice
        self.model_dir = os.path.join(os.path.dirname(__file__), "models")
        self.model_path = os.path.join(self.model_dir, "kokoro-v1.0.onnx")
        self.voices_path = os.path.join(self.model_dir, "voices-v1.0.bin")
        
        self._ensure_models_downloaded()
        
        try:
            # We import here so the application can start even if kokoro-onnx isn't installed yet
            from kokoro_onnx import Kokoro
            self.kokoro = Kokoro(self.model_path, self.voices_path)
            logger.info(f"Successfully loaded Kokoro ONNX model with voice '{self.voice}'")
        except ImportError as e:
            raise VoiceGenerationException("kokoro-onnx package is not installed. Please run: pip install kokoro-onnx soundfile misaki") from e
        except Exception as e:
            raise VoiceGenerationException(f"Failed to load Kokoro ONNX model: {str(e)}") from e

    def _ensure_models_downloaded(self):
        os.makedirs(self.model_dir, exist_ok=True)
        
        files = {
            "kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
            "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
        }
        
        for filename, url in files.items():
            file_path = os.path.join(self.model_dir, filename)
            if not os.path.exists(file_path):
                logger.info(f"Downloading Kokoro TTS dependency '{filename}' to {file_path}. This is a one-time download and may take a few minutes...")
                try:
                    urllib.request.urlretrieve(url, file_path)
                    logger.info(f"Successfully downloaded {filename}.")
                except Exception as e:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    raise VoiceGenerationException(f"Failed to download {filename}: {str(e)}")

    def synthesize(self, text: str) -> bytes:
        try:
            # Generate the raw audio samples (numpy array)
            # kokoro-onnx streams by default, but calling create(..., speed=1.0) 
            # returns a generator if we use the stream API, or just array if we use create
            # According to docs: kokoro.create(text, voice="af_heart", speed=1.0, lang="en-us")
            
            samples, sample_rate = self.kokoro.create(
                text, voice=self.voice, speed=1.0, lang="en-us"
            )
            
            if len(samples) == 0:
                raise ValueError("Kokoro generated empty audio array.")
                
            # Convert numpy array to WAV bytes in memory
            buffer = io.BytesIO()
            sf.write(buffer, samples, sample_rate, format='WAV')
            buffer.seek(0)
            
            return buffer.read()
            
        except Exception as e:
            raise VoiceGenerationException(f"Kokoro synthesis failed: {str(e)}") from e
