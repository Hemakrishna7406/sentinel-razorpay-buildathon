"""
Sentinel — Natural Language Policy Compiler

Parses human-written policy rules into executable predicates.
This is NOT an LLM wrapper. It is a deterministic DSL compiler that translates
structured natural-language-like strings into Python lambda predicates.

Example rules:
    "ESCALATE IF amount > 5000000"
    "ESCALATE IF action_type = refund AND amount > 1000000"
    "ESCALATE IF hour_of_day < 6 OR hour_of_day > 22"
    "ESCALATE IF recipient_novelty = 1 AND amount > 2000000"

Grammar (BNF-ish):
    rule       := "ESCALATE IF" condition
    condition  := clause (("AND"|"OR") clause)*
    clause     := field operator value
    field      := identifier
    operator   := ">" | ">=" | "<" | "<=" | "=" | "!="
    value      := number | string
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Supported operators mapped to Python comparisons
OPERATORS = {
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    "=": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}

# Regex to tokenize a single clause: field operator value
CLAUSE_RE = re.compile(r"(\w+)\s*(>=|<=|!=|>|<|=)\s*(\S+)")


@dataclass
class PolicyClause:
    """A single comparison: field op value."""

    field: str
    operator: str
    value: Any

    def evaluate(self, context: Dict[str, Any]) -> bool:
        actual = context.get(self.field)
        if actual is None:
            # Missing field → fail-closed: clause evaluates True → ESCALATE
            return True
        op_fn = OPERATORS[self.operator]
        return op_fn(actual, self.value)

    def __str__(self):
        return f"{self.field} {self.operator} {self.value}"


@dataclass
class PolicyRule:
    """A compiled rule: ESCALATE IF clause (AND|OR clause)*."""

    raw_text: str
    clauses: List[PolicyClause]
    connectors: List[str]  # "AND" or "OR" between clauses
    rule_id: str = ""

    def evaluate(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Evaluate the rule against a context dict.
        Returns (should_escalate, reason).
        """
        if not self.clauses:
            return False, ""

        result = self.clauses[0].evaluate(context)

        for i, connector in enumerate(self.connectors):
            clause_result = self.clauses[i + 1].evaluate(context)
            if connector == "AND":
                result = result and clause_result
            else:  # OR
                result = result or clause_result

        if result:
            return True, f"Policy rule triggered: {self.raw_text}"
        return False, ""

    def __str__(self):
        return self.raw_text


def _parse_value(raw: str) -> Any:
    """Parse a string value into int, float, or keep as string."""
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    # Strip surrounding quotes if present
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    return raw


def compile_rule(text: str, rule_id: str = "") -> PolicyRule:
    """
    Compile a natural language rule string into an executable PolicyRule.

    Args:
        text: The rule text, e.g. "ESCALATE IF amount > 5000000"
        rule_id: Optional identifier for this rule.

    Returns:
        A PolicyRule that can evaluate a context dict.

    Raises:
        ValueError: If the rule text is malformed.
    """
    text = text.strip()

    # Normalize: uppercase the keywords
    upper = text.upper()
    if not upper.startswith("ESCALATE IF"):
        raise ValueError(f"Rule must start with 'ESCALATE IF'. Got: {text}")

    # Extract the condition portion
    condition_str = text[len("ESCALATE IF") :].strip()

    if not condition_str:
        raise ValueError("Rule has no condition after 'ESCALATE IF'.")

    # Split by AND/OR, preserving the connectors
    tokens = re.split(r"\b(AND|OR)\b", condition_str, flags=re.IGNORECASE)

    clauses = []
    connectors = []

    for token in tokens:
        token = token.strip()
        if not token:
            continue
        if token.upper() in ("AND", "OR"):
            connectors.append(token.upper())
        else:
            match = CLAUSE_RE.match(token)
            if not match:
                raise ValueError(f"Cannot parse clause: '{token}'")
            field_name = match.group(1)
            operator = match.group(2)
            value = _parse_value(match.group(3))
            clauses.append(PolicyClause(field=field_name, operator=operator, value=value))

    if len(clauses) == 0:
        raise ValueError(f"No valid clauses found in rule: {text}")

    if len(connectors) != len(clauses) - 1:
        raise ValueError(f"Mismatch between clauses ({len(clauses)}) and connectors ({len(connectors)}).")

    return PolicyRule(
        raw_text=text, clauses=clauses, connectors=connectors, rule_id=rule_id or f"rule_{hash(text) % 10000:04d}"
    )


class NLPolicyCompiler:
    """
    Manages a set of compiled NL policy rules.
    Rules are evaluated in order. First matching rule triggers ESCALATE.
    """

    def __init__(self):
        self.rules: List[PolicyRule] = []

    def add_rule(self, text: str, rule_id: str = "") -> PolicyRule:
        """Compile and add a rule."""
        rule = compile_rule(text, rule_id)
        self.rules.append(rule)
        logger.info(f"Compiled policy rule [{rule.rule_id}]: {rule.raw_text}")
        return rule

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID."""
        before = len(self.rules)
        self.rules = [r for r in self.rules if r.rule_id != rule_id]
        return len(self.rules) < before

    def evaluate(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Evaluate all rules against a context.
        Returns (should_escalate, reason) — first matching rule wins.
        """
        for rule in self.rules:
            should_escalate, reason = rule.evaluate(context)
            if should_escalate:
                return True, reason
        return False, ""

    def list_rules(self) -> List[Dict[str, str]]:
        """Return all rules as serializable dicts."""
        return [{"rule_id": r.rule_id, "text": r.raw_text} for r in self.rules]

    def clear(self):
        """Remove all rules."""
        self.rules.clear()
