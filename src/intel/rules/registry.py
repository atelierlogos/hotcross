"""Registry for language extraction rules."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.intel.rules.base import LanguageRules


class RuleRegistry:
    """Registry mapping languages and file extensions to extraction rules.

    Usage:
        # Register rules
        RuleRegistry.register(PythonRules())

        # Get rules for a file
        rules = RuleRegistry.get_for_file("src/main.py")
        if rules:
            symbols = list(rules.extract_symbols(tree, source))
    """

    _rules: dict[str, LanguageRules] = {}
    _extension_map: dict[str, str] = {}

    @classmethod
    def register(cls, rules: LanguageRules) -> None:
        """Register language rules.

        Args:
            rules: Language rules implementation
        """
        cls._rules[rules.language] = rules
        for ext in rules.file_extensions:
            cls._extension_map[ext] = rules.language

    @classmethod
    def get_for_language(cls, language: str) -> LanguageRules | None:
        """Get rules for a language.

        Args:
            language: Language identifier (e.g., 'python')

        Returns:
            Language rules or None if not registered
        """
        return cls._rules.get(language)

    @classmethod
    def get_for_file(cls, file_path: str) -> LanguageRules | None:
        """Get rules for a file based on its extension.

        Args:
            file_path: Path to the source file

        Returns:
            Language rules or None if not supported
        """
        ext = Path(file_path).suffix.lower()
        language = cls._extension_map.get(ext)
        return cls._rules.get(language) if language else None

    @classmethod
    def get_language_for_file(cls, file_path: str) -> str | None:
        """Get the language identifier for a file.

        Args:
            file_path: Path to the source file

        Returns:
            Language identifier or None if not supported
        """
        ext = Path(file_path).suffix.lower()
        return cls._extension_map.get(ext)

    @classmethod
    def supported_extensions(cls) -> list[str]:
        """Get all supported file extensions.

        Returns:
            List of file extensions (e.g., ['.py', '.js'])
        """
        return list(cls._extension_map.keys())

    @classmethod
    def supported_languages(cls) -> list[str]:
        """Get all supported languages.

        Returns:
            List of language identifiers
        """
        return list(cls._rules.keys())

    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        """Check if a file is supported.

        Args:
            file_path: Path to the source file

        Returns:
            True if the file extension is supported
        """
        ext = Path(file_path).suffix.lower()
        return ext in cls._extension_map

    @classmethod
    def clear(cls) -> None:
        """Clear all registered rules (mainly for testing)."""
        cls._rules.clear()
        cls._extension_map.clear()
