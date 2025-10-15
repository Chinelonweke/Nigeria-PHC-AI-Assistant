"""
Translation Service
Handles translation between English and Nigerian languages using NLLB-200
"""

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import Dict, Optional
import torch

from backend.core.logger import get_logger
from backend.services.cache_service import cache_service

logger = get_logger(__name__)

# Language codes for NLLB-200
LANGUAGE_CODES = {
    'english': 'eng_Latn',
    'hausa': 'hau_Latn',
    'yoruba': 'yor_Latn',
    'igbo': 'ibo_Latn',
    'pidgin': 'eng_Latn',  # Pidgin uses English script
}

class TranslationService:
    """Translation service using NLLB-200"""
    
    def __init__(self):
        """Initialize translation service"""
        self.model_name = "facebook/nllb-200-distilled-600M"
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        try:
            logger.info(f"🌍 Loading NLLB-200 translation model on {self.device}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name).to(self.device)
            logger.info("✅ Translation Service initialized")
        except Exception as e:
            logger.error(f"❌ Failed to load translation model: {e}")
            logger.warning("⚠️ Translation will use fallback mode")
    
    def translate(
        self, 
        text: str, 
        source_lang: str = 'english', 
        target_lang: str = 'hausa'
    ) -> str:
        """
        Translate text between languages
        
        Args:
            text: Text to translate
            source_lang: Source language (english, hausa, yoruba, igbo, pidgin)
            target_lang: Target language
            
        Returns:
            Translated text
        """
        try:
            # Check cache
            cache_key = f"translate_{text[:50]}_{source_lang}_{target_lang}"
            cached = cache_service.get(cache_key)
            if cached:
                logger.info("✅ Using cached translation")
                return cached
            
            if not self.model or not self.tokenizer:
                logger.warning("⚠️ Translation model not available, returning original")
                return text
            
            # Get language codes
            src_code = LANGUAGE_CODES.get(source_lang.lower(), 'eng_Latn')
            tgt_code = LANGUAGE_CODES.get(target_lang.lower(), 'hau_Latn')
            
            logger.info(f"🌍 Translating: {source_lang} → {target_lang}")
            
            # Tokenize
            self.tokenizer.src_lang = src_code
            inputs = self.tokenizer(text, return_tensors="pt", padding=True).to(self.device)
            
            # Generate translation
            translated_tokens = self.model.generate(
                **inputs,
                forced_bos_token_id=self.tokenizer.lang_code_to_id[tgt_code],
                max_length=512
            )
            
            # Decode
            translated_text = self.tokenizer.batch_decode(
                translated_tokens, 
                skip_special_tokens=True
            )[0]
            
            # Cache result
            cache_service.set(cache_key, translated_text, ttl=3600)
            
            logger.info(f"✅ Translation complete")
            return translated_text
            
        except Exception as e:
            logger.error(f"❌ Translation error: {e}")
            return text
    
    def translate_to_english(self, text: str, source_lang: str) -> str:
        """Translate any language to English"""
        return self.translate(text, source_lang, 'english')
    
    def translate_from_english(self, text: str, target_lang: str) -> str:
        """Translate English to any language"""
        return self.translate(text, 'english', target_lang)


# Global instance
translation_service = TranslationService()