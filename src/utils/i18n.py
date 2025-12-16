"""
i18n.py - Internationalization Support Module
국제화 지원 모듈

Provides multi-language support for Korean, English, and Vietnamese.
한국어, 영어, 베트남어에 대한 다국어 지원을 제공합니다.

Core Features / 핵심 기능:
- Load translations from JSON configuration / JSON 설정에서 번역 로드
- Dynamic language switching / 동적 언어 전환
- Fallback to default language if translation missing / 번역 누락 시 기본 언어로 대체
- Nested key support (e.g., "cards.total_employees") / 중첩 키 지원
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path


class I18n:
    """
    Internationalization manager for multi-language support
    다국어 지원을 위한 국제화 관리자
    """

    def __init__(self, config_path: Optional[str] = None, default_lang: str = "ko"):
        """
        Initialize I18n with translations configuration
        번역 설정으로 I18n 초기화

        Args:
            config_path: Path to translations.json file / translations.json 파일 경로
            default_lang: Default language code (ko/en/vi) / 기본 언어 코드
        """
        self.default_lang = default_lang
        self.current_lang = default_lang
        self.translations: Dict[str, Dict] = {}

        # Set default config path if not provided / 제공되지 않으면 기본 설정 경로 설정
        if config_path is None:
            # Assume config is in HR/config/translations.json
            hr_root = Path(__file__).parent.parent.parent
            config_path = hr_root / "config" / "translations.json"

        self.config_path = Path(config_path)
        self._load_translations()

    def _load_translations(self) -> None:
        """
        Load translations from JSON file
        JSON 파일에서 번역 로드

        Raises:
            FileNotFoundError: If translations file doesn't exist / 번역 파일이 없는 경우
            json.JSONDecodeError: If JSON is invalid / JSON이 유효하지 않은 경우
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Translations file not found / 번역 파일을 찾을 수 없습니다: {self.config_path}"
            )

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.translations = json.load(f)

        # Validate that default language exists / 기본 언어가 존재하는지 검증
        if self.default_lang not in self.translations:
            raise ValueError(
                f"Default language '{self.default_lang}' not found in translations / "
                f"번역에서 기본 언어 '{self.default_lang}'를 찾을 수 없습니다"
            )

    def set_language(self, lang: str) -> None:
        """
        Set current language
        현재 언어 설정

        Args:
            lang: Language code (ko/en/vi) / 언어 코드

        Raises:
            ValueError: If language not supported / 지원되지 않는 언어인 경우
        """
        if lang not in self.translations:
            raise ValueError(
                f"Language '{lang}' not supported / 언어 '{lang}'는 지원되지 않습니다. "
                f"Available / 사용 가능: {list(self.translations.keys())}"
            )
        self.current_lang = lang

    def get_language(self) -> str:
        """
        Get current language code
        현재 언어 코드 반환

        Returns:
            Current language code / 현재 언어 코드
        """
        return self.current_lang

    def t(self, key: str, lang: Optional[str] = None, **kwargs) -> str:
        """
        Translate a key to current or specified language
        키를 현재 또는 지정된 언어로 번역

        Supports nested keys with dot notation: "cards.total_employees"
        점 표기법으로 중첩 키 지원: "cards.total_employees"

        Args:
            key: Translation key (supports dot notation) / 번역 키 (점 표기법 지원)
            lang: Language code (uses current if None) / 언어 코드 (None이면 현재 언어 사용)
            **kwargs: Format parameters for string interpolation / 문자열 보간을 위한 형식 매개변수

        Returns:
            Translated string or key if not found / 번역된 문자열 또는 찾을 수 없으면 키 반환

        Examples:
            >>> i18n = I18n()
            >>> i18n.t("dashboard_title")  # "HR 관리 대시보드"
            >>> i18n.t("cards.total_employees")  # "총 인원"
            >>> i18n.t("metrics.count", count=5)  # "5명"
        """
        target_lang = lang or self.current_lang

        # Navigate nested keys / 중첩 키 탐색
        keys = key.split('.')
        value = self.translations.get(target_lang, {})

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                value = None
                break

        # Fallback to default language if translation not found
        # 번역을 찾을 수 없으면 기본 언어로 대체
        if value is None and target_lang != self.default_lang:
            value = self.translations.get(self.default_lang, {})
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    value = None
                    break

        # Return key itself if still not found / 여전히 찾을 수 없으면 키 자체 반환
        if value is None:
            return key

        # Handle string interpolation / 문자열 보간 처리
        if isinstance(value, str) and kwargs:
            try:
                return value.format(**kwargs)
            except KeyError:
                return value

        return str(value)

    def get_all_translations(self, lang: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all translations for a language
        특정 언어의 모든 번역 반환

        Args:
            lang: Language code (uses current if None) / 언어 코드 (None이면 현재 언어)

        Returns:
            Dictionary of all translations / 모든 번역의 딕셔너리
        """
        target_lang = lang or self.current_lang
        return self.translations.get(target_lang, {})

    def get_supported_languages(self) -> list:
        """
        Get list of supported language codes
        지원되는 언어 코드 목록 반환

        Returns:
            List of language codes / 언어 코드 목록
        """
        return list(self.translations.keys())

    def reload_translations(self) -> None:
        """
        Reload translations from file (useful for development)
        파일에서 번역 다시 로드 (개발에 유용)
        """
        self._load_translations()


# Global instance for easy access / 쉬운 접근을 위한 전역 인스턴스
_global_i18n: Optional[I18n] = None


def init_i18n(config_path: Optional[str] = None, default_lang: str = "ko") -> I18n:
    """
    Initialize global i18n instance
    전역 i18n 인스턴스 초기화

    Args:
        config_path: Path to translations.json / translations.json 경로
        default_lang: Default language code / 기본 언어 코드

    Returns:
        Initialized I18n instance / 초기화된 I18n 인스턴스
    """
    global _global_i18n
    _global_i18n = I18n(config_path, default_lang)
    return _global_i18n


def get_i18n() -> I18n:
    """
    Get global i18n instance
    전역 i18n 인스턴스 반환

    Returns:
        Global I18n instance / 전역 I18n 인스턴스

    Raises:
        RuntimeError: If i18n not initialized / i18n이 초기화되지 않은 경우
    """
    global _global_i18n
    if _global_i18n is None:
        raise RuntimeError(
            "I18n not initialized. Call init_i18n() first / "
            "I18n이 초기화되지 않았습니다. 먼저 init_i18n()을 호출하세요"
        )
    return _global_i18n


def t(key: str, lang: Optional[str] = None, **kwargs) -> str:
    """
    Convenience function for translation using global instance
    전역 인스턴스를 사용한 번역 편의 함수

    Args:
        key: Translation key / 번역 키
        lang: Language code / 언어 코드
        **kwargs: Format parameters / 형식 매개변수

    Returns:
        Translated string / 번역된 문자열
    """
    return get_i18n().t(key, lang, **kwargs)
