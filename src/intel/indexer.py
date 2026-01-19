"""Code indexer orchestration for Memory Portals."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.intel.graph import CodeGraph
from src.intel.parser import CodeParser
from src.intel.rules.registry import RuleRegistry

if TYPE_CHECKING:
    from src.core.portal import MemoryPortal

logger = logging.getLogger(__name__)


class IndexStats:
    """Statistics from an indexing operation."""

    def __init__(self):
        self.files_indexed = 0
        self.files_skipped = 0
        self.files_failed = 0
        self.symbols_extracted = 0
        self.types_extracted = 0
        self.imports_extracted = 0
        self.exports_extracted = 0
        self.scopes_extracted = 0
        self.references_extracted = 0
        self.total_duration_ms = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "files_indexed": self.files_indexed,
            "files_skipped": self.files_skipped,
            "files_failed": self.files_failed,
            "symbols_extracted": self.symbols_extracted,
            "types_extracted": self.types_extracted,
            "imports_extracted": self.imports_extracted,
            "exports_extracted": self.exports_extracted,
            "scopes_extracted": self.scopes_extracted,
            "references_extracted": self.references_extracted,
            "total_duration_ms": self.total_duration_ms,
        }


class CodeIndexer:
    """Orchestrates code indexing using tree-sitter and language rules."""

    def __init__(self, portal: MemoryPortal, project_id: str | None = None):
        """Initialize the indexer.

        Args:
            portal: Memory portal for storage
            project_id: Optional project ID for all indexing operations
        """
        self.portal = portal
        self.graph = CodeGraph(portal, project_id=project_id)
        self.parser = CodeParser()
        self.project_id = project_id

    @staticmethod
    def compute_file_hash(file_path: Path) -> str:
        """Compute SHA-256 hash of file contents.

        Args:
            file_path: Path to file

        Returns:
            Hex digest of file hash
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def should_index_file(self, file_path: Path) -> tuple[bool, str | None]:
        """Check if file should be indexed (based on hash).

        Args:
            file_path: Path to file

        Returns:
            Tuple of (should_index, reason)
        """
        if not file_path.exists():
            return False, "file_not_found"

        # Check if we support this file type
        rules = RuleRegistry.get_for_file(str(file_path))
        if rules is None:
            return False, "unsupported_language"

        # Compute current hash
        try:
            current_hash = self.compute_file_hash(file_path)
        except Exception as e:
            logger.warning(f"Failed to hash {file_path}: {e}")
            return False, "hash_error"

        # Check if file is already indexed with same hash
        existing_hash = self.graph.get_file_hash(str(file_path))
        if existing_hash and existing_hash == current_hash:
            return False, "unchanged"

        return True, None

    def index_file(self, file_path: str | Path, force: bool = False) -> dict[str, Any]:
        """Index a single source file.

        Args:
            file_path: Path to source file
            force: Force re-indexing even if unchanged

        Returns:
            Dictionary with indexing results
        """
        import time

        file_path = Path(file_path)
        start_time = time.perf_counter()

        # Check if we should index
        if not force:
            should_index, reason = self.should_index_file(file_path)
            if not should_index:
                logger.debug(f"Skipping {file_path}: {reason}")
                return {
                    "file_path": str(file_path),
                    "status": "skipped",
                    "reason": reason,
                }

        # Get language rules
        rules = RuleRegistry.get_for_file(str(file_path))
        if rules is None:
            return {
                "file_path": str(file_path),
                "status": "failed",
                "error": "unsupported_language",
            }

        try:
            # Read file content
            with open(file_path, "rb") as f:
                source = f.read()

            # Parse with tree-sitter
            tree = self.parser.parse(source, rules.language)
            if tree is None:
                return {
                    "file_path": str(file_path),
                    "status": "failed",
                    "error": "parse_failed",
                }

            # Extract all entities
            symbols = list(rules.extract_symbols(tree, source))
            types = list(rules.extract_types(tree, source))
            imports = list(rules.extract_imports(tree, source))
            exports = list(rules.extract_exports(tree, source))
            scopes = list(rules.extract_scopes(tree, source))
            references = list(rules.extract_references(tree, source))

            # Compute file hash
            content_hash = self.compute_file_hash(file_path)

            # Store in graph
            parse_duration = (time.perf_counter() - start_time) * 1000

            self.graph.store_file_info(
                file_path=str(file_path),
                language=rules.language,
                content_hash=content_hash,
                line_count=source.count(b"\n") + 1,
                byte_size=len(source),
                parse_duration_ms=parse_duration,
            )

            # Store all extracted entities
            for symbol in symbols:
                self.graph.store_symbol(str(file_path), symbol)

            for type_info in types:
                self.graph.store_type(str(file_path), type_info)

            for import_info in imports:
                self.graph.store_import(str(file_path), import_info)

            for export_info in exports:
                self.graph.store_export(str(file_path), export_info)

            for scope in scopes:
                self.graph.store_scope(str(file_path), scope)

            for reference in references:
                self.graph.store_reference(str(file_path), reference)

            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                f"Indexed {file_path}: {len(symbols)} symbols, "
                f"{len(types)} types, {len(imports)} imports in {duration_ms:.1f}ms"
            )

            return {
                "file_path": str(file_path),
                "status": "indexed",
                "symbols": len(symbols),
                "types": len(types),
                "imports": len(imports),
                "exports": len(exports),
                "scopes": len(scopes),
                "references": len(references),
                "duration_ms": duration_ms,
            }

        except Exception as e:
            logger.error(f"Failed to index {file_path}: {e}", exc_info=True)
            return {
                "file_path": str(file_path),
                "status": "failed",
                "error": str(e),
            }

    def index_directory(
        self,
        directory: str | Path,
        recursive: bool = True,
        force: bool = False,
        file_patterns: list[str] | None = None,
    ) -> IndexStats:
        """Index all supported files in a directory.

        Args:
            directory: Directory path
            recursive: Recursively index subdirectories
            force: Force re-indexing of all files
            file_patterns: Optional list of glob patterns to match

        Returns:
            IndexStats with indexing results
        """
        import time

        directory = Path(directory)
        stats = IndexStats()
        start_time = time.perf_counter()

        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return stats

        # Get all supported file extensions
        supported_extensions = RuleRegistry.supported_extensions()

        # Find files to index
        if recursive:
            files = []
            for ext in supported_extensions:
                files.extend(directory.rglob(f"*{ext}"))
        else:
            files = []
            for ext in supported_extensions:
                files.extend(directory.glob(f"*{ext}"))

        # Apply file patterns if provided
        if file_patterns:
            filtered_files = []
            for file in files:
                for pattern in file_patterns:
                    if file.match(pattern):
                        filtered_files.append(file)
                        break
            files = filtered_files

        logger.info(f"Found {len(files)} files to index in {directory}")

        # Index each file
        for file_path in files:
            result = self.index_file(file_path, force=force)

            if result["status"] == "indexed":
                stats.files_indexed += 1
                stats.symbols_extracted += result.get("symbols", 0)
                stats.types_extracted += result.get("types", 0)
                stats.imports_extracted += result.get("imports", 0)
                stats.exports_extracted += result.get("exports", 0)
                stats.scopes_extracted += result.get("scopes", 0)
                stats.references_extracted += result.get("references", 0)
            elif result["status"] == "skipped":
                stats.files_skipped += 1
            elif result["status"] == "failed":
                stats.files_failed += 1

        stats.total_duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"Indexing complete: {stats.files_indexed} indexed, "
            f"{stats.files_skipped} skipped, {stats.files_failed} failed "
            f"in {stats.total_duration_ms:.1f}ms"
        )

        return stats


    def index_documents(
        self,
        directory: str | Path,
        recursive: bool = True,
        patterns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Index documentation files in a directory.

        Args:
            directory: Directory path
            recursive: Recursively search subdirectories
            patterns: File patterns to match (default: README*, *.md, *.rst, docs/*)

        Returns:
            Dictionary with indexing statistics
        """
        directory = Path(directory)
        
        if patterns is None:
            patterns = [
                "README*",
                "*.md",
                "*.markdown",
                "*.rst",
                "*.txt",
                "CONTRIBUTING*",
                "CHANGELOG*",
                "LICENSE*",
                "docs/**/*",
            ]

        files_indexed = 0
        files_skipped = 0
        total_words = 0

        # Find documentation files
        doc_files = []
        for pattern in patterns:
            if recursive:
                doc_files.extend(directory.rglob(pattern))
            else:
                doc_files.extend(directory.glob(pattern))

        # Filter to only files (not directories) and exclude database files
        doc_files = [
            f for f in doc_files 
            if f.is_file() and ".db" not in str(f) and "store/" not in str(f)
        ]

        logger.info(f"Found {len(doc_files)} documentation files")

        for file_path in doc_files:
            try:
                # Read content
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                
                # Determine document type
                doc_type = self._infer_doc_type(file_path)
                
                # Extract title (first heading or filename)
                title = self._extract_title(content, file_path)
                
                # Determine format
                format = file_path.suffix.lstrip(".") or "txt"
                
                # Store document
                self.graph.store_document(
                    file_path=str(file_path),
                    content=content,
                    doc_type=doc_type,
                    title=title,
                    format=format,
                )
                
                files_indexed += 1
                total_words += len(content.split())
                
            except Exception as e:
                logger.warning(f"Failed to index document {file_path}: {e}")
                files_skipped += 1

        logger.info(
            f"Indexed {files_indexed} documents ({total_words} words), "
            f"skipped {files_skipped}"
        )

        return {
            "files_indexed": files_indexed,
            "files_skipped": files_skipped,
            "total_words": total_words,
        }

    def _infer_doc_type(self, file_path: Path) -> str:
        """Infer document type from filename."""
        name_lower = file_path.name.lower()
        
        if name_lower.startswith("readme"):
            return "readme"
        elif name_lower.startswith("contributing"):
            return "contributing"
        elif name_lower.startswith("changelog"):
            return "changelog"
        elif name_lower.startswith("license"):
            return "license"
        elif "api" in name_lower:
            return "api"
        elif "guide" in name_lower or "tutorial" in name_lower:
            return "guide"
        elif file_path.parent.name == "docs":
            return "documentation"
        else:
            return "general"

    def _extract_title(self, content: str, file_path: Path) -> str | None:
        """Extract title from document content."""
        lines = content.split("\n")
        
        # Look for markdown heading
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line.startswith("# "):
                return line.lstrip("# ").strip()
            elif line.startswith("=") and len(line) > 3:
                # RST style heading (previous line is title)
                idx = lines.index(line)
                if idx > 0:
                    return lines[idx - 1].strip()
        
        # Fallback to filename
        return file_path.stem.replace("-", " ").replace("_", " ").title()
