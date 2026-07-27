import os
import wave
from app.core.exceptions import VoiceGenerationException
from app.domain.models.audio_clip import AudioClip
from app.domain.models.narration_segment import NarrationSegment
from app.infrastructure.audio.base import TTSProvider
from app.infrastructure.audio.kokoro_tts_provider import KokoroTTSProvider

class AudioBuilder:
    """
    Synthesizes narration text using a TTSProvider (Kokoro v1.0) and measures real duration
    from the output audio file.
    """
    def __init__(self, provider: TTSProvider | None = None) -> None:
        self.provider = provider or KokoroTTSProvider()

    def synthesize(self, segment: NarrationSegment, output_dir: str) -> AudioClip:
        if not segment.narration_text:
            raise VoiceGenerationException(f"Cannot synthesize empty narration text for unit {segment.unit_id}")

        # Ensure output audio directory exists
        audio_dir = os.path.join(output_dir, "audio")
        os.makedirs(audio_dir, exist_ok=True)

        # Kokoro generates high-quality WAV files, not MP3
        file_path = os.path.join(audio_dir, f"{segment.unit_id}.wav")

        try:
            # 1. Synthesize audio bytes
            audio_bytes = self.provider.synthesize(segment.narration_text)
            
            if not audio_bytes or len(audio_bytes) == 0:
                raise VoiceGenerationException(f"Received empty audio bytes from TTS provider for unit {segment.unit_id}")

            # 2. Write file to disk
            with open(file_path, "wb") as f:
                f.write(audio_bytes)

            # 3. Sanity check on file size
            if os.path.getsize(file_path) == 0:
                raise VoiceGenerationException(f"Generated audio file is 0 bytes for unit {segment.unit_id}")

            # 4. Measure real duration from the WAV file using built-in wave module
            try:
                with wave.open(file_path, 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    rate = wav_file.getframerate()
                    duration = frames / float(rate)
            except Exception as e:
                raise VoiceGenerationException(f"Failed to read WAV duration (corrupt audio output): {str(e)}") from e

            # 5. Sanity check duration
            if duration <= 0:
                raise VoiceGenerationException(f"Measured audio duration is 0 or negative: {duration}s")

            return AudioClip(
                unit_id=segment.unit_id,
                storage_path=file_path,
                duration_sec=round(duration, 2)
            )

        except Exception as e:
            if not isinstance(e, VoiceGenerationException):
                raise VoiceGenerationException(f"Audio synthesis failed for unit {segment.unit_id}: {str(e)}") from e
            raise
