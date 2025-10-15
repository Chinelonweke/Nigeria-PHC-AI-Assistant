"""
Text-to-Speech Service
Converts text to speech using Coqui TTS
"""

from TTS.api import TTS
from pathlib import Path
import tempfile
from typing import Optional

from backend.core.config import settings
from backend.core.logger import get_logger

logger = get_logger(__name__)


class TTSService:
    """
    Service for text-to-speech using Coqui TTS
    
    Features:
    - Multiple language support
    - Natural-sounding voice
    - Audio file generation
    """
    
    def __init__(self):
        """Initialize TTS model"""
        try:
            logger.info("🔊 Initializing TTS Service...")
            logger.info("   This may take a few minutes on first run...")
            
            # Initialize TTS with English model
            # Coqui TTS has limited support for Nigerian languages
            # For best results with English
            self.tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
            
            logger.info("✅ TTS Service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize TTS: {e}")
            raise
    
    def text_to_speech(
        self,
        text: str,
        output_path: Optional[str] = None,
        language: str = 'en'
    ) -> str:
        """
        Convert text to speech audio file
        
        Args:
            text: Text to convert
            output_path: Where to save audio file (optional, uses temp if None)
            language: Language code (currently only 'en' well-supported)
        
        Returns:
            Path to generated audio file
            
        Example:
            >>> tts = TTSService()
            >>> audio_path = tts.text_to_speech(
            ...     "Please take this medication twice daily",
            ...     output_path="instruction.wav"
            ... )
            >>> print(audio_path)
            'instruction.wav'
        """
        try:
            logger.info(f"🔊 Converting text to speech: '{text[:50]}...'")
            
            # Create output path if not provided
            if output_path is None:
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix='.wav'
                )
                output_path = temp_file.name
                temp_file.close()
            
            output_path = Path(output_path)
            
            # Create parent directories if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate speech
            self.tts.tts_to_file(
                text=text,
                file_path=str(output_path)
            )
            
            logger.info(f"✅ Audio generated: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ TTS error: {e}")
            raise
    
    def text_to_speech_bytes(self, text: str) -> bytes:
        """
        Convert text to speech and return as bytes
        (Useful for API responses)
        
        Args:
            text: Text to convert
        
        Returns:
            Audio file as bytes
            
        Example:
            >>> audio_bytes = tts.text_to_speech_bytes("Hello world")
            >>> # Send bytes over API
        """
        try:
            # Generate to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Generate audio
            self.text_to_speech(text, output_path=temp_path)
            
            # Read file as bytes
            with open(temp_path, 'rb') as f:
                audio_bytes = f.read()
            
            # Clean up
            Path(temp_path).unlink()
            
            return audio_bytes
            
        except Exception as e:
            logger.error(f"❌ Error generating audio bytes: {e}")
            raise
    
    def get_available_languages(self) -> list:
        """
        Get list of available TTS languages/models
        
        Returns:
            List of available models
        """
        try:
            return TTS().list_models()
        except:
            return ['tts_models/en/ljspeech/tacotron2-DDC']


# Global instance
tts_service = TTSService()


# Test function
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TTS SERVICE TEST")
    print("=" * 60 + "\n")
    
    try:
        service = TTSService()
        
        # Test 1: Generate speech
        print("🔊 Test 1: Text-to-Speech")
        test_text = "Hello, this is a test of the text to speech service."
        
        output_file = "test_output/test_speech.wav"
        Path("test_output").mkdir(exist_ok=True)
        
        audio_path = service.text_to_speech(test_text, output_path=output_file)
        
        print(f"  Generated audio: {audio_path}")
        print(f"  File exists: {Path(audio_path).exists()}")
        print(f"  File size: {Path(audio_path).stat().st_size / 1024:.2f} KB")
        
        # Test 2: Generate as bytes
        print("\n📦 Test 2: Generate Audio Bytes")
        audio_bytes = service.text_to_speech_bytes("Testing bytes output")
        print(f"  Generated {len(audio_bytes)} bytes")
        
        print("\n✅ All tests passed!")
        print(f"\n🎧 Play the audio file: {audio_path}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    
    print("\n" + "=" * 60)