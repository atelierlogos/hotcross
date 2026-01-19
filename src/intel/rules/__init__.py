"""Language-specific extraction rules for code intelligence.

This module provides a registry of language rules that define how to
extract symbols, types, imports, exports, scopes, and references from
source code using tree-sitter.
"""

from src.intel.rules.base import BaseLanguageRules, LanguageRules
from src.intel.rules.javascript import JavaScriptRules, TypeScriptRules
from src.intel.rules.python import PythonRules
from src.intel.rules.registry import RuleRegistry

# Register language rules
RuleRegistry.register(PythonRules())
RuleRegistry.register(JavaScriptRules())
RuleRegistry.register(TypeScriptRules())

__all__ = [
    "BaseLanguageRules",
    "LanguageRules",
    "RuleRegistry",
    "PythonRules",
    "JavaScriptRules",
    "TypeScriptRules",
]
