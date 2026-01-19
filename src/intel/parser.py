"""Tree-sitter parser wrapper for code intelligence."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tree_sitter import Language, Parser, Tree


class CodeParser:
    """Wrapper around tree-sitter for parsing source code.

    This class handles:
    - Loading language grammars
    - Parsing source files
    - Caching parsers per language
    """

    _parsers: dict[str, Parser] = {}
    _languages: dict[str, Language] = {}

    @classmethod
    def get_parser(cls, language: str) -> Parser:
        """Get or create a parser for a language.

        Args:
            language: Language identifier (e.g., 'python', 'javascript')

        Returns:
            Configured tree-sitter parser

        Raises:
            ValueError: If the language is not supported
        """
        if language not in cls._parsers:
            cls._parsers[language] = cls._create_parser(language)
        return cls._parsers[language]

    @classmethod
    def _create_parser(cls, language: str) -> Parser:
        """Create a new parser for a language.

        Args:
            language: Language identifier

        Returns:
            Configured parser

        Raises:
            ValueError: If the language grammar is not available
        """
        from tree_sitter import Parser, Language

        lang = cls._get_language(language)
        parser = Parser(Language(lang))
        return parser

    @classmethod
    def _get_language(cls, language: str) -> Any:
        """Get the tree-sitter Language object for a language.

        Args:
            language: Language identifier

        Returns:
            tree-sitter Language object

        Raises:
            ValueError: If the language is not supported
        """
        if language not in cls._languages:
            cls._languages[language] = cls._load_language(language)
        return cls._languages[language]

    @classmethod
    def _load_language(cls, language: str) -> Any:
        """Load a tree-sitter language grammar.

        Args:
            language: Language identifier

        Returns:
            tree-sitter Language object

        Raises:
            ValueError: If the language is not supported
        """
        # Map language names to tree-sitter-{lang} packages
        language_map = {
            "python": "tree_sitter_python",
            "javascript": "tree_sitter_javascript",
            "typescript": "tree_sitter_typescript",
            "tsx": "tree_sitter_typescript",
        }

        module_name = language_map.get(language)
        if not module_name:
            raise ValueError(f"Unsupported language: {language}")

        try:
            import importlib
            module = importlib.import_module(module_name)

            # Handle typescript which has multiple languages
            if language == "typescript":
                return module.language_typescript()
            elif language == "tsx":
                return module.language_tsx()
            else:
                # Standard pattern: module.language()
                return module.language()
        except ImportError as e:
            raise ValueError(
                f"Language grammar not installed for '{language}'. "
                f"Install with: pip install tree-sitter-{language}"
            ) from e

    @classmethod
    def parse(cls, source: bytes, language: str) -> Tree:
        """Parse source code into a syntax tree.

        Args:
            source: Source code as bytes
            language: Language identifier

        Returns:
            Parsed syntax tree
        """
        parser = cls.get_parser(language)
        return parser.parse(source)

    @classmethod
    def parse_file(cls, file_path: str | Path, language: str | None = None) -> tuple[Tree, bytes]:
        """Parse a source file.

        Args:
            file_path: Path to the source file
            language: Language identifier (auto-detected if not provided)

        Returns:
            Tuple of (syntax tree, source bytes)

        Raises:
            ValueError: If language cannot be determined
            FileNotFoundError: If file does not exist
        """
        path = Path(file_path)

        if language is None:
            language = cls._detect_language(path)
            if language is None:
                raise ValueError(f"Cannot determine language for: {path}")

        source = path.read_bytes()
        tree = cls.parse(source, language)
        return tree, source

    @classmethod
    def _detect_language(cls, path: Path) -> str | None:
        """Detect language from file extension.

        Args:
            path: File path

        Returns:
            Language identifier or None
        """
        ext_to_lang = {
            ".py": "python",
            ".pyi": "python",
            ".js": "javascript",
            ".mjs": "javascript",
            ".cjs": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "tsx",
        }
        return ext_to_lang.get(path.suffix.lower())

    @classmethod
    def supported_languages(cls) -> list[str]:
        """Get list of supported languages.

        Returns:
            List of language identifiers
        """
        return ["python", "javascript", "typescript", "tsx"]

    @classmethod
    def clear_cache(cls) -> None:
        """Clear cached parsers and languages (mainly for testing)."""
        cls._parsers.clear()
        cls._languages.clear()
