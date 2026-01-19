"""JavaScript/TypeScript language extraction rules using tree-sitter."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Iterator

from src.intel.rules.base import (
    BaseLanguageRules,
    ExportInfo,
    ImportInfo,
    ReferenceInfo,
    ScopeInfo,
    SymbolInfo,
    TypeInfo,
)

if TYPE_CHECKING:
    from tree_sitter import Node, Tree

logger = logging.getLogger(__name__)


class JavaScriptRules(BaseLanguageRules):
    """JavaScript language extraction rules."""

    language = "javascript"
    file_extensions = (".js", ".jsx", ".mjs", ".cjs")

    def extract_symbols(self, tree: Tree, source: bytes) -> Iterator[SymbolInfo]:
        """Extract functions, classes, methods, and variables."""
        root = tree.root_node
        yield from self._extract_symbols_recursive(root, source)

    def _extract_symbols_recursive(
        self, node: Node, source: bytes, parent_id: str | None = None
    ) -> Iterator[SymbolInfo]:
        """Recursively extract symbols."""
        # Function declarations
        if node.type == "function_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = source[name_node.start_byte : name_node.end_byte].decode("utf-8")
                
                # Check if async
                is_async = any(child.type == "async" for child in node.children)
                
                yield SymbolInfo(
                    name=name,
                    qualified_name=name,
                    kind="function",
                    visibility="public",
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    start_col=node.start_point[1],
                    end_col=node.end_point[1],
                    parent_symbol_id=parent_id,
                    is_async=is_async,
                )

        # Arrow functions assigned to variables
        elif node.type == "variable_declarator":
            name_node = node.child_by_field_name("name")
            value_node = node.child_by_field_name("value")
            
            if name_node and value_node and value_node.type in ("arrow_function", "function"):
                name = source[name_node.start_byte : name_node.end_byte].decode("utf-8")
                is_async = any(child.type == "async" for child in value_node.children)
                
                yield SymbolInfo(
                    name=name,
                    qualified_name=name,
                    kind="function",
                    visibility=self._infer_visibility(name),
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    start_col=node.start_point[1],
                    end_col=node.end_point[1],
                    parent_symbol_id=parent_id,
                    is_async=is_async,
                )

        # Class declarations
        elif node.type == "class_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = source[name_node.start_byte : name_node.end_byte].decode("utf-8")
                class_id = f"{name}_{node.start_point[0]}"
                
                yield SymbolInfo(
                    name=name,
                    qualified_name=name,
                    kind="class",
                    visibility="public",
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    start_col=node.start_point[1],
                    end_col=node.end_point[1],
                    parent_symbol_id=parent_id,
                )
                
                # Extract methods
                body = node.child_by_field_name("body")
                if body:
                    for child in body.children:
                        if child.type == "method_definition":
                            yield from self._extract_method(child, source, class_id)

        # Recurse
        for child in node.children:
            yield from self._extract_symbols_recursive(child, source, parent_id)

    def _extract_method(self, node: Node, source: bytes, class_id: str) -> Iterator[SymbolInfo]:
        """Extract a class method."""
        name_node = node.child_by_field_name("name")
        if name_node:
            name = source[name_node.start_byte : name_node.end_byte].decode("utf-8")
            
            # Check if static or async
            is_static = any(child.type == "static" for child in node.children)
            is_async = any(child.type == "async" for child in node.children)
            
            yield SymbolInfo(
                name=name,
                qualified_name=name,
                kind="method",
                visibility="public",
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                start_col=node.start_point[1],
                end_col=node.end_point[1],
                parent_symbol_id=class_id,
                is_static=is_static,
                is_async=is_async,
            )

    def extract_types(self, tree: Tree, source: bytes) -> Iterator[TypeInfo]:
        """Extract type annotations (for TypeScript compatibility)."""
        # JavaScript doesn't have native types, but we can extract JSDoc types
        return iter([])

    def extract_imports(self, tree: Tree, source: bytes) -> Iterator[ImportInfo]:
        """Extract import statements."""
        root = tree.root_node
        yield from self._extract_imports_recursive(root, source)

    def _extract_imports_recursive(self, node: Node, source: bytes) -> Iterator[ImportInfo]:
        """Recursively extract imports."""
        if node.type == "import_statement":
            # import { x, y } from 'module'
            source_node = node.child_by_field_name("source")
            if source_node:
                module_path = source[source_node.start_byte : source_node.end_byte].decode("utf-8")
                module_path = module_path.strip("\"'")
                
                # Extract imported names
                imported_names = []
                for child in node.children:
                    if child.type == "import_clause":
                        for spec in child.children:
                            if spec.type == "named_imports":
                                for import_spec in spec.children:
                                    if import_spec.type == "import_specifier":
                                        name_node = import_spec.child_by_field_name("name")
                                        if name_node:
                                            name = source[name_node.start_byte : name_node.end_byte].decode("utf-8")
                                            imported_names.append(name)
                
                yield ImportInfo(
                    module_path=module_path,
                    imported_names=imported_names,
                    import_kind="import",
                    start_line=node.start_point[0] + 1,
                )

        # require() calls
        elif node.type == "call_expression":
            func = node.child_by_field_name("function")
            if func and source[func.start_byte : func.end_byte].decode("utf-8") == "require":
                args = node.child_by_field_name("arguments")
                if args and len(args.children) > 0:
                    arg = args.children[0]
                    if arg.type == "string":
                        module_path = source[arg.start_byte : arg.end_byte].decode("utf-8")
                        module_path = module_path.strip("\"'")
                        
                        yield ImportInfo(
                            module_path=module_path,
                            imported_names=[],
                            import_kind="require",
                            start_line=node.start_point[0] + 1,
                        )

        for child in node.children:
            yield from self._extract_imports_recursive(child, source)

    def extract_exports(self, tree: Tree, source: bytes) -> Iterator[ExportInfo]:
        """Extract export statements."""
        root = tree.root_node
        yield from self._extract_exports_recursive(root, source)

    def _extract_exports_recursive(self, node: Node, source: bytes) -> Iterator[ExportInfo]:
        """Recursively extract exports."""
        if node.type == "export_statement":
            # export { x, y }
            for child in node.children:
                if child.type == "export_clause":
                    for spec in child.children:
                        if spec.type == "export_specifier":
                            name_node = spec.child_by_field_name("name")
                            if name_node:
                                name = source[name_node.start_byte : name_node.end_byte].decode("utf-8")
                                yield ExportInfo(
                                    exported_name=name,
                                    export_kind="direct",
                                    start_line=node.start_point[0] + 1,
                                )
                # export default
                elif child.type == "default":
                    yield ExportInfo(
                        exported_name="default",
                        export_kind="default",
                        start_line=node.start_point[0] + 1,
                    )

        for child in node.children:
            yield from self._extract_exports_recursive(child, source)

    def extract_scopes(self, tree: Tree, source: bytes) -> Iterator[ScopeInfo]:
        """Extract lexical scopes."""
        root = tree.root_node
        
        # Module-level scope
        yield ScopeInfo(
            kind="module",
            name=None,
            start_line=1,
            end_line=root.end_point[0] + 1,
            depth=0,
        )
        
        yield from self._extract_scopes_recursive(root, source, depth=1)

    def _extract_scopes_recursive(
        self, node: Node, source: bytes, depth: int, parent_id: str | None = None
    ) -> Iterator[ScopeInfo]:
        """Recursively extract scopes."""
        if node.type in ("function_declaration", "arrow_function", "function", "class_declaration"):
            name = None
            if node.type in ("function_declaration", "class_declaration"):
                name_node = node.child_by_field_name("name")
                if name_node:
                    name = source[name_node.start_byte : name_node.end_byte].decode("utf-8")
            
            kind = "class" if node.type == "class_declaration" else "function"
            
            yield ScopeInfo(
                kind=kind,
                name=name,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                depth=depth,
                parent_scope_id=parent_id,
            )
            
            scope_id = f"{name}_{node.start_point[0]}" if name else f"anon_{node.start_point[0]}"
            
            for child in node.children:
                yield from self._extract_scopes_recursive(child, source, depth + 1, scope_id)
        else:
            for child in node.children:
                yield from self._extract_scopes_recursive(child, source, depth, parent_id)

    def extract_references(self, tree: Tree, source: bytes) -> Iterator[ReferenceInfo]:
        """Extract symbol references."""
        root = tree.root_node
        yield from self._extract_references_recursive(root, source)

    def _extract_references_recursive(self, node: Node, source: bytes) -> Iterator[ReferenceInfo]:
        """Recursively extract references."""
        if node.type == "identifier":
            name = source[node.start_byte : node.end_byte].decode("utf-8")
            
            kind = "read"
            if node.parent:
                if node.parent.type == "call_expression":
                    kind = "call"
                elif node.parent.type in ("assignment_expression", "variable_declarator"):
                    kind = "write"
            
            yield ReferenceInfo(
                name=name,
                kind=kind,
                start_line=node.start_point[0] + 1,
                start_col=node.start_point[1],
            )

        for child in node.children:
            yield from self._extract_references_recursive(child, source)

    def _infer_visibility(self, name: str) -> str:
        """Infer visibility from naming convention."""
        if name.startswith("_"):
            return "private"
        return "public"


class TypeScriptRules(JavaScriptRules):
    """TypeScript language extraction rules (extends JavaScript)."""

    language = "typescript"
    file_extensions = (".ts", ".tsx")

    def extract_types(self, tree: Tree, source: bytes) -> Iterator[TypeInfo]:
        """Extract TypeScript type annotations and interfaces."""
        root = tree.root_node
        yield from self._extract_types_recursive(root, source)

    def _extract_types_recursive(self, node: Node, source: bytes) -> Iterator[TypeInfo]:
        """Recursively extract type definitions."""
        # Type aliases: type MyType = ...
        if node.type == "type_alias_declaration":
            name_node = node.child_by_field_name("name")
            value_node = node.child_by_field_name("value")
            
            if name_node:
                name = source[name_node.start_byte : name_node.end_byte].decode("utf-8")
                type_expr = ""
                if value_node:
                    type_expr = source[value_node.start_byte : value_node.end_byte].decode("utf-8")
                
                yield TypeInfo(
                    name=name,
                    kind="alias",
                    type_expression=type_expr,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                )

        # Interfaces: interface MyInterface { ... }
        elif node.type == "interface_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = source[name_node.start_byte : name_node.end_byte].decode("utf-8")
                
                yield TypeInfo(
                    name=name,
                    kind="interface",
                    type_expression="interface",
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                )

        for child in node.children:
            yield from self._extract_types_recursive(child, source)
