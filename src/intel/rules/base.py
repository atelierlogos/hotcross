"""Base classes and protocols for language extraction rules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Iterator, Protocol, runtime_checkable

if TYPE_CHECKING:
    from tree_sitter import Node, Tree

from src.models.code_intel import (
    ExportInfo,
    ImportInfo,
    ReferenceInfo,
    ScopeInfo,
    SymbolInfo,
    TypeInfo,
)


@runtime_checkable
class LanguageRules(Protocol):
    """Protocol defining the interface for language-specific extraction rules."""

    @property
    def language(self) -> str:
        """The language identifier (e.g., 'python', 'javascript')."""
        ...

    @property
    def file_extensions(self) -> tuple[str, ...]:
        """File extensions for this language (e.g., ('.py',))."""
        ...

    def extract_symbols(self, tree: Tree, source: bytes) -> Iterator[SymbolInfo]:
        """Extract symbol definitions from the syntax tree."""
        ...

    def extract_types(self, tree: Tree, source: bytes) -> Iterator[TypeInfo]:
        """Extract type annotations and aliases from the syntax tree."""
        ...

    def extract_imports(self, tree: Tree, source: bytes) -> Iterator[ImportInfo]:
        """Extract import statements from the syntax tree."""
        ...

    def extract_exports(self, tree: Tree, source: bytes) -> Iterator[ExportInfo]:
        """Extract exports from the syntax tree."""
        ...

    def extract_scopes(self, tree: Tree, source: bytes) -> Iterator[ScopeInfo]:
        """Extract lexical scopes from the syntax tree."""
        ...

    def extract_references(self, tree: Tree, source: bytes) -> Iterator[ReferenceInfo]:
        """Extract symbol references from the syntax tree."""
        ...


class BaseLanguageRules(ABC):
    """Abstract base class for language-specific extraction rules.

    Provides common utility methods for working with tree-sitter nodes.
    """

    @property
    @abstractmethod
    def language(self) -> str:
        """The language identifier."""
        ...

    @property
    @abstractmethod
    def file_extensions(self) -> tuple[str, ...]:
        """File extensions for this language."""
        ...

    @abstractmethod
    def extract_symbols(self, tree: Tree, source: bytes) -> Iterator[SymbolInfo]:
        """Extract symbol definitions."""
        ...

    @abstractmethod
    def extract_types(self, tree: Tree, source: bytes) -> Iterator[TypeInfo]:
        """Extract type annotations and aliases."""
        ...

    @abstractmethod
    def extract_imports(self, tree: Tree, source: bytes) -> Iterator[ImportInfo]:
        """Extract import statements."""
        ...

    @abstractmethod
    def extract_exports(self, tree: Tree, source: bytes) -> Iterator[ExportInfo]:
        """Extract exports."""
        ...

    @abstractmethod
    def extract_scopes(self, tree: Tree, source: bytes) -> Iterator[ScopeInfo]:
        """Extract lexical scopes."""
        ...

    @abstractmethod
    def extract_references(self, tree: Tree, source: bytes) -> Iterator[ReferenceInfo]:
        """Extract symbol references."""
        ...

    # --- Utility methods ---

    def get_node_text(self, node: Node, source: bytes) -> str:
        """Get the text content of a node."""
        return source[node.start_byte:node.end_byte].decode("utf-8")

    def get_node_location(self, node: Node) -> tuple[int, int, int, int]:
        """Get (start_line, end_line, start_col, end_col) for a node.

        Lines are 1-indexed, columns are 0-indexed.
        """
        return (
            node.start_point[0] + 1,  # 1-indexed line
            node.end_point[0] + 1,    # 1-indexed line
            node.start_point[1],      # 0-indexed column
            node.end_point[1],        # 0-indexed column
        )

    def find_child_by_type(self, node: Node, type_name: str) -> Node | None:
        """Find the first child node of a specific type."""
        for child in node.children:
            if child.type == type_name:
                return child
        return None

    def find_children_by_type(self, node: Node, type_name: str) -> list[Node]:
        """Find all child nodes of a specific type."""
        return [child for child in node.children if child.type == type_name]

    def find_child_by_field(self, node: Node, field_name: str) -> Node | None:
        """Find a child node by field name."""
        return node.child_by_field_name(field_name)

    def walk_tree(self, node: Node) -> Iterator[Node]:
        """Walk all nodes in the tree depth-first."""
        yield node
        for child in node.children:
            yield from self.walk_tree(child)

    def find_nodes_by_type(self, tree: Tree, type_name: str) -> Iterator[Node]:
        """Find all nodes of a specific type in the tree."""
        for node in self.walk_tree(tree.root_node):
            if node.type == type_name:
                yield node
