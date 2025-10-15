"""
Whisper Speech-to-Text Service
Converts audio to text in multiple languages
"""

import whisper
import torch
from pathlib import Path
from typing import Optional, Dict
import tempfile
import os

from backend.core.config import settings
from backend.core.logger import get_logger

logger = get_logger(__name__)


class WhisperService:
    """
    Service for speech-to-text using OpenAI Whisper
    
    Features:
    - Multiple language support
    - Audio file processing
    - Real-time transcription
    - Language detection
    """
    
    def __init__(self, model_size: str = None):
        """
        Initialize Whisper model
        
        Args:
            model_size: Model size (tiny, base, small, medium, large)
                       Default from settings (base is good for most cases)
        """
        try:
            self.model_size = model_size or settings.WHISPER_MODEL
            
            logger.info(f"🎤 Loading Whisper model: {self.model_size}")
            logger.info("   This may take a few minutes on first run...")
            
            # Load model
            self.model = whisper.load_model(self.model_size)
            
            # Check if GPU is available
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"   Using device: {self.device}")
            
            logger.info("✅ Whisper Service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Whisper: {e}")
            raise
    
    def transcribe_audio(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> Dict:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to audio file (mp3, wav, m4a, etc.)
            language: Language code (en, ha, yo, ig, etc.) or None for auto-detect
            task: 'transcribe' or 'translate' (translate converts to English)
        
        Returns:
            Dictionary with transcription results
            
        Example:
            >>> whisper_service = WhisperService()
            >>> result = whisper_service.transcribe_audio('patient_recording.mp3', language='en')
            >>> print(result['text'])
            'Patient complains of fever and headache'
        """
        try:
            audio_path = Path(audio_path)
            
            if not audio_path.exists():
                logger.error(f"❌ Audio file not found: {audio_path}")
                return {'error': 'File not found'}
            
            logger.info(f"🎤 Transcribing: {audio_path.name}")
            
            # Prepare options
            options = {'task': task}
            if language:
                options['language'] = language
            
            # Transcribe
            result = self.model.transcribe(
                str(audio_path),
                **options
            )
            
            # Extract information
            transcription = {
                'text': result['text'].strip(),
                'language': result.get('language', 'unknown'),
                'segments': [
                    {
                        'start': seg['start'],
                        'end': seg['end'],
                        'text': seg['text'].strip()
                    }
                    for seg in result.get('segments', [])
                ],
                'duration': result.get('segments', [{}])[-1].get('end', 0) if result.get('segments') else 0
            }
            
            logger.info(f"✅ Transcription complete")
            logger.info(f"   Language: {transcription['language']}")
            logger.info(f"   Text length: {len(transcription['text'])} characters")
            
            return transcription
            
        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            return {'error': str(e)}
    
    def transcribe_bytes(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None,
        file_extension: str = '.wav'
    ) -> Dict:
        """
        Transcribe audio from bytes (useful for API uploads)
        
        Args:
            audio_bytes: Audio file as bytes
            language: Language code
            file_extension: Audio format extension
        
        Returns:
            Transcription results
            
        Example:
            >>> with open('audio.wav', 'rb') as f:
            ...     audio_bytes = f.read()
            >>> result = whisper_service.transcribe_bytes(audio_bytes, language='en')
        """
        try:
            # Save to temporary file
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=file_extension
            ) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name
            
            # Transcribe
            result = self.transcribe_audio(temp_path, language=language)
            
            # Clean up
            os.unlink(temp_path)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error transcribing bytes: {e}")
            return {'error': str(e)}
    
    def detect_language(self, audio_path: str) -> str:
        """
        Detect language in audio file
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Language code (e.g., 'en', 'ha', 'yo')
            
        Example:
            >>> lang = whisper_service.detect_language('patient_audio.wav')
            >>> print(lang)
            'ha'  # Hausa detected
        """
        try:
            logger.info(f"🔍 Detecting language in: {audio_path}")
            
            # Load audio
            audio = whisper.load_audio(str(audio_path))
            audio = whisper.pad_or_trim(audio)
            
            # Make log-Mel spectrogram
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
            
            # Detect language
            _, probs = self.model.detect_language(mel)
            detected_language = max(probs, key=probs.get)
            
            logger.info(f"✅ Detected language: {detected_language} ({probs[detected_language]:.2%} confidence)")
            
            return detected_language
            
        except Exception as e:
            logger.error(f"❌ Language detection error: {e}")
            return 'en'  # Default to English
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get list of supported languages
        
        Returns:
            Dictionary of language codes and names
        """
        return {
            'en': 'English',
            'ha': 'Hausa',
            'yo': 'Yoruba',
            'ig': 'Igbo',
            'pcm': 'Nigerian Pidgin',
            'fr': 'French',
            'ar': 'Arabic',
            'es': 'Spanish',
            'pt': 'Portuguese',
            'zh': 'Chinese',
            # Whisper supports 99+ languages
        }


# Global instance
whisper_service = WhisperService()


# Test function
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("WHISPER SERVICE TEST")
    print("=" * 60 + "\n")
    
    try:
        service = WhisperService(model_size='base')
        
        # Test 1: Model info
        print("📋 Test 1: Model Information")
        print(f"  Model size: {service.model_size}")
        print(f"  Device: {service.device}")
        
        # Test 2: Supported languages
        print("\n🌍 Test 2: Supported Languages")
        languages = service.get_supported_languages()
        print(f"  Nigerian languages supported:")
        for code, name in languages.items():
            if code in ['en', 'ha', 'yo', 'ig', 'pcm']:
                print(f"    {code}: {name}")
        
        # Test 3: Would test transcription but need audio file
        print("\n🎤 Test 3: Transcription")
        print("  ⚠️ Note: Need audio file to test transcription")
        print("  Usage example:")
        print("    result = service.transcribe_audio('audio.mp3', language='en')")
        print("    print(result['text'])")
        
        print("\n✅ Service ready for use!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    
    print("\n" + "=" * 60)