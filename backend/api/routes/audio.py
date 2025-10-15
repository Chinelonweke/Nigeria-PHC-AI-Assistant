"""
Audio Processing Routes
Handles voice transcription (STT) and text-to-speech (TTS)
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask  # ✅ CORRECT IMPORT
import tempfile
import os

from backend.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Form("english")
):
    """
    Transcribe audio to text using Whisper
    
    Args:
        audio: Audio file (WAV, MP3, etc.)
        language: Language hint (english, hausa, yoruba, igbo, pidgin)
        
    Returns:
        JSON with transcribed text
    """
    try:
        logger.info(f"🎤 Transcribing audio ({language})")
        
        # Import Whisper
        try:
            import whisper
        except ImportError:
            logger.error("❌ Whisper not installed")
            raise HTTPException(
                status_code=500,
                detail="Whisper not installed. Run: pip install openai-whisper"
            )
        
        # Save uploaded file to temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            content = await audio.read()
            temp_audio.write(content)
            temp_path = temp_audio.name
        
        # Load Whisper model
        logger.info("🔄 Loading Whisper model...")
        model = whisper.load_model("base")
        
        # Transcribe
        logger.info("🔄 Transcribing...")
        result = model.transcribe(temp_path, language=language[:2])  # Use 2-letter code
        
        # Clean up
        os.remove(temp_path)
        
        transcribed_text = result["text"]
        logger.info(f"✅ Transcription complete: {transcribed_text[:50]}...")
        
        return {
            "success": True,
            "text": transcribed_text,
            "language": language
        }
        
    except Exception as e:
        logger.error(f"❌ Transcription error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/text-to-speech")
async def text_to_speech(
    text: str = Form(...),
    language: str = Form("english")
):
    """
    Convert text to speech using Google TTS
    
    Args:
        text: Text to convert to speech
        language: Language (english, hausa, yoruba, igbo, pidgin)
        
    Returns:
        Audio file (MP3)
    """
    try:
        logger.info(f"🔊 Converting text to speech ({language})")
        logger.info(f"📝 Text: {text[:100]}...")
        
        # Import gTTS
        try:
            from gtts import gTTS
        except ImportError:
            logger.error("❌ gTTS not installed")
            raise HTTPException(
                status_code=500,
                detail="gTTS not installed. Run: pip install gtts"
            )
        
        # Map languages to gTTS codes
        language_map = {
            'english': 'en',
            'hausa': 'ha',
            'yoruba': 'yo',
            'igbo': 'ig',
            'pidgin': 'en'  # Use English for Pidgin
        }
        
        lang_code = language_map.get(language.lower(), 'en')
        logger.info(f"🌍 Using language code: {lang_code}")
        
        # Generate speech
        logger.info("🔄 Generating speech...")
        tts = gTTS(text=text, lang=lang_code, slow=False)
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_path = temp_audio.name
        
        tts.save(temp_path)
        logger.info(f"💾 Saved to: {temp_path}")
        
        # Check file exists and has content
        if not os.path.exists(temp_path):
            raise Exception("Failed to generate audio file")
        
        file_size = os.path.getsize(temp_path)
        logger.info(f"📦 Audio file size: {file_size} bytes")
        
        if file_size == 0:
            raise Exception("Generated audio file is empty")
        
        logger.info("✅ TTS generation complete")
        
        # Cleanup function
        def cleanup():
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    logger.info(f"🗑️ Cleaned up temp file")
            except Exception as e:
                logger.warning(f"⚠️ Cleanup failed: {e}")
        
        # Return audio file with background cleanup
        return FileResponse(
            path=temp_path,
            media_type="audio/mpeg",
            filename="response.mp3",
            background=BackgroundTask(cleanup)
        )
        
    except Exception as e:
        logger.error(f"❌ TTS error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"TTS failed: {str(e)}"
        )


@router.get("/health")
async def audio_health():
    """
    Check if audio services are available
    
    Returns:
        Status of Whisper and gTTS services
    """
    status = {
        "whisper": False,
        "gtts": False
    }
    
    try:
        import whisper
        status["whisper"] = True
    except ImportError:
        pass
    
    try:
        from gtts import gTTS
        status["gtts"] = True
    except ImportError:
        pass
    
    return {
        "status": "ok",
        "services": status,
        "message": f"Whisper: {'✅' if status['whisper'] else '❌'}, gTTS: {'✅' if status['gtts'] else '❌'}"
    }