"""Python language extraction rules using tree-sitter."""

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


class PythonRules(BaseLanguageRules):
    """Python language extraction rules."""

    language = "python"
    file_extensions = (".py", ".pyi")

    def extract_symbols(self, tree: Tree, source: bytes) -> Iterator[SymbolInfo]:
        """Extract functions, classes, methods, and variables."""
        root = tree.root_node

        # Extract functions
        yield from self._extract_functions(root, source)

        # Extract classes
        yield from self._extract_classes(root, source)

    def _extract_functions(
        self, node: Node, source: bytes, parent_id: str | None = None
    ) -> Iterator[SymbolInfo]:
        """Extract function definitions."""
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = source[name_node.start_byte : name_node.end_byte].decode("utf-8")

                # Get decorators
                decorators = []
                for child in node.children:
                    if child.type == "decorator":
                        dec_text = source[child.start_byte : child.end_byte].decode("utf-8")
                        decorators.append(dec_text.strip())

                # Check if async
                is_async = any(child.type == "async" for child in node.children)

                # Get docstring
                docstring = self._extract_docstring(node, source)

                # Get signature
                params_node = node.child_by_field_name("parameters")
                return_type_node = node.child_by_field_name("return_type")
                signature = self._build_function_signature(
                    name, params_node, return_type_node, source
                )

                yield SymbolInfo(
                    name=name,
                    qualified_name=name,  # Will be updated with parent context
                    kind="function" if parent_id is None else "method",
                    visibility=self._infer_visibility(name),
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    start_col=node.start_point[1],
                    end_col=node.end_point[1],
                    parent_symbol_id=parent_id,
                    docstring=docstring,
                    signature=signature,
                    is_async=is_async,
                    decorators=decorators,
                )

        # Recurse into children
        for child in node.children:
            yield from self._extract_functions(child, source, parent_id)

    def _extract_classes(self, node: Node, source: bytes) -> Iterator[SymbolInfo]:
        """Extract class definitions."""
        if node.type == "class_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = source[name_node.start_byte : name_node.end_byte].decode("utf-8")

                # Get decorators
                decorators = []
                for child in node.children:
                    if child.type == "decorator":
                        dec_text = source[child.start_byte : child.end_byte].decode("utf-8")
                        decorators.append(dec_text.strip())

                # Get docstring
                docstring = self._extract_docstring(node, source)

                # Get base classes
                bases = []
                superclasses_node = node.child_by_field_name("superclasses")
                if superclasses_node:
                    for arg in superclasses_node.children:
                        if arg.type == "identifier":
                            bases.append(
                                source[arg.start_byte : arg.end_byte].decode("utf-8")
                            )

                signature = f"class {name}({', '.join(bases)})" if bases else f"class {name}"

                class_id = f"{name}_{node.start_point[0]}"

                yield SymbolInfo(
                    name=name,
                    qualified_name=name,
                    kind="class",
                    visibility=self._infer_visibility(name),
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    start_col=node.start_point[1],
                    end_col=node.end_point[1],
                    docstring=docstring,
                    signature=signature,
                    decorators=decorators,
                )

                # Extract methods within this class
                body = node.child_by_field_name("body")
                if body:
                    for child in body.children:
                        if child.type == "function_definition":
                            yield from self._extract_functions(child, source, class_id)

        # Recurse into children (but not into class bodies, handled above)
        for child in node.children:
            if node.type != "class_definition" or child.type != "block":
                yield from self._extract_classes(child, source)

    def extract_types(self, tree: Tree, source: bytes) -> Iterator[TypeInfo]:
        """Extract type annotations and aliases."""
        root = tree.root_node
        yield from self._extract_type_aliases(root, source)
        yield from self._extract_annotations(root, source)

    def _extract_type_aliases(self, node: Node, source: bytes) -> Iterator[TypeInfo]:
        """Extract type alias assignments."""
        if node.type == "assignment":
            # Look for pattern: TypeName = SomeType
            left = node.child_by_field_name("left")
            right = node.child_by_field_name("right")

            if left and right and left.type == "identifier":
                name = source[left.start_byte : left.end_byte].decode("utf-8")
                # Check if name starts with uppercase (convention for type aliases)
                if name[0].isupper():
                    type_expr = source[right.start_byte : right.end_byte].decode("utf-8")
                    yield TypeInfo(
                        name=name,
                        kind="alias",
                        type_expression=type_expr,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                    )

        for child in node.children:
            yield from self._extract_type_aliases(child, source)

    def _extract_annotations(self, node: Node, source: bytes) -> Iterator[TypeInfo]:
        """Extract type annotations from function parameters and return types."""
        if node.type == "type":
            type_expr = source[node.start_byte : node.end_byte].decode("utf-8")
            yield TypeInfo(
                name="",  # Anonymous annotation
                kind="annotation",
                type_expression=type_expr,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
            )

        for child in node.children:
            yield from self._extract_annotations(child, source)

    def extract_imports(self, tree: Tree, source: bytes) -> Iterator[ImportInfo]:
        """Extract import statements."""
        root = tree.root_node
        yield from self._extract_imports_recursive(root, source)

    def _extract_imports_recursive(self, node: Node, source: bytes) -> Iterator[ImportInfo]:
        """Recursively extract imports."""
        if node.type == "import_statement":
            # import module [as alias]
            for child in node.children:
                if child.type == "dotted_name":
                    module = source[child.start_byte : child.end_byte].decode("utf-8")
                    yield ImportInfo(
                        module_path=module,
                        imported_names=[],
                        import_kind="import",
                        start_line=node.start_point[0] + 1,
                    )

        elif node.type == "import_from_statement":
            # from module import name [as alias]
            module_node = node.child_by_field_name("module_name")
            module_path = ""
            is_relative = False
            relative_level = 0

            if module_node:
                module_path = source[module_node.start_byte : module_node.end_byte].decode(
                    "utf-8"
                )

            # Check for relative imports (leading dots)
            for child in node.children:
                if child.type == "relative_import":
                    is_relative = True
                    relative_level = source[child.start_byte : child.end_byte].count(b".")

            # Extract imported names
            imported_names = []
            for child in node.children:
                if child.type == "dotted_name" and child != module_node:
                    name = source[child.start_byte : child.end_byte].decode("utf-8")
                    imported_names.append(name)
                elif child.type == "aliased_import":
                    name_node = child.child_by_field_name("name")
                    if name_node:
                        name = source[name_node.start_byte : name_node.end_byte].decode("utf-8")
                        imported_names.append(name)

            yield ImportInfo(
                module_path=module_path,
                imported_names=imported_names,
                import_kind="from_import",
                is_relative=is_relative,
                relative_level=relative_level,
                start_line=node.start_point[0] + 1,
            )

        for child in node.children:
            yield from self._extract_imports_recursive(child, source)

    def extract_exports(self, tree: Tree, source: bytes) -> Iterator[ExportInfo]:
        """Extract exports via __all__ analysis."""
        root = tree.root_node
        yield from self._extract_all_exports(root, source)

    def _extract_all_exports(self, node: Node, source: bytes) -> Iterator[ExportInfo]:
        """Extract __all__ list."""
        if node.type == "assignment":
            left = node.child_by_field_name("left")
            right = node.child_by_field_name("right")

            if left and right:
                left_text = source[left.start_byte : left.end_byte].decode("utf-8")
                if left_text == "__all__":
                    # Parse the list
                    if right.type == "list":
                        for child in right.children:
                            if child.type == "string":
                                # Remove quotes
                                name = source[child.start_byte : child.end_byte].decode("utf-8")
                                name = name.strip("\"'")
                                yield ExportInfo(
                                    exported_name=name,
                                    export_kind="direct",
                                    start_line=child.start_point[0] + 1,
                                )

        for child in node.children:
            yield from self._extract_all_exports(child, source)

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

        # Extract nested scopes
        yield from self._extract_scopes_recursive(root, source, depth=1)

    def _extract_scopes_recursive(
        self, node: Node, source: bytes, depth: int, parent_id: str | None = None
    ) -> Iterator[ScopeInfo]:
        """Recursively extract scopes."""
        if node.type in ("function_definition", "class_definition"):
            name_node = node.child_by_field_name("name")
            name = None
            if name_node:
                name = source[name_node.start_byte : name_node.end_byte].decode("utf-8")

            kind = "function" if node.type == "function_definition" else "class"

            yield ScopeInfo(
                kind=kind,
                name=name,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                depth=depth,
                parent_scope_id=parent_id,
            )

            scope_id = f"{name}_{node.start_point[0]}" if name else f"anon_{node.start_point[0]}"

            # Recurse into body
            body = node.child_by_field_name("body")
            if body:
                for child in body.children:
                    yield from self._extract_scopes_recursive(child, source, depth + 1, scope_id)

        else:
            for child in node.children:
                yield from self._extract_scopes_recursive(child, source, depth, parent_id)

    def extract_references(self, tree: Tree, source: bytes) -> Iterator[ReferenceInfo]:
        """Extract symbol references (unresolved)."""
        root = tree.root_node
        yield from self._extract_references_recursive(root, source)

    def _extract_references_recursive(self, node: Node, source: bytes) -> Iterator[ReferenceInfo]:
        """Recursively extract references."""
        if node.type == "identifier":
            name = source[node.start_byte : node.end_byte].decode("utf-8")

            # Determine reference kind based on parent
            kind = "read"
            if node.parent:
                if node.parent.type == "call":
                    kind = "call"
                elif node.parent.type == "assignment" and node == node.parent.child_by_field_name(
                    "left"
                ):
                    kind = "write"

            yield ReferenceInfo(
                name=name,
                kind=kind,
                start_line=node.start_point[0] + 1,
                start_col=node.start_point[1],
            )

        for child in node.children:
            yield from self._extract_references_recursive(child, source)

    # Helper methods

    def _extract_docstring(self, node: Node, source: bytes) -> str | None:
        """Extract docstring from a function or class."""
        body = node.child_by_field_name("body")
        if body and len(body.children) > 0:
            first_stmt = body.children[0]
            if first_stmt.type == "expression_statement":
                expr = first_stmt.children[0] if first_stmt.children else None
                if expr and expr.type == "string":
                    docstring = source[expr.start_byte : expr.end_byte].decode("utf-8")
                    # Remove quotes and clean up
                    docstring = docstring.strip("\"'")
                    return docstring
        return None

    def _build_function_signature(
        self,
        name: str,
        params_node: Node | None,
        return_type_node: Node | None,
        source: bytes,
    ) -> str:
        """Build function signature string."""
        params = ""
        if params_node:
            params = source[params_node.start_byte : params_node.end_byte].decode("utf-8")

        return_type = ""
        if return_type_node:
            return_type = (
                " -> " + source[return_type_node.start_byte : return_type_node.end_byte].decode("utf-8")
            )

        return f"{name}{params}{return_type}"

    def _infer_visibility(self, name: str) -> str:
        """Infer visibility from naming convention."""
        if name.startswith("__") and not name.endswith("__"):
            return "private"
        elif name.startswith("_"):
            return "protected"
        else:
            return "public"
