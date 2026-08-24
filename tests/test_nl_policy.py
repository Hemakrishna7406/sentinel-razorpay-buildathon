"""
Tests for the Natural Language Policy Compiler.
"""

import pytest
from security.nl_policy import compile_rule, NLPolicyCompiler


class TestCompileRule:
    def test_simple_amount_rule(self):
        rule = compile_rule("ESCALATE IF amount > 5000000")
        assert len(rule.clauses) == 1
        assert rule.clauses[0].field == "amount"
        assert rule.clauses[0].operator == ">"
        assert rule.clauses[0].value == 5000000

    def test_and_rule(self):
        rule = compile_rule("ESCALATE IF action_type = refund AND amount > 1000000")
        assert len(rule.clauses) == 2
        assert rule.connectors == ["AND"]

    def test_or_rule(self):
        rule = compile_rule("ESCALATE IF hour_of_day < 6 OR hour_of_day > 22")
        assert len(rule.clauses) == 2
        assert rule.connectors == ["OR"]

    def test_invalid_prefix(self):
        with pytest.raises(ValueError, match="ESCALATE IF"):
            compile_rule("BLOCK IF amount > 100")

    def test_empty_condition(self):
        with pytest.raises(ValueError, match="no condition"):
            compile_rule("ESCALATE IF")


class TestRuleEvaluation:
    def test_amount_escalation_true(self):
        rule = compile_rule("ESCALATE IF amount > 5000000")
        escalate, reason = rule.evaluate({"amount": 6000000})
        assert escalate is True
        assert "Policy rule triggered" in reason

    def test_amount_escalation_false(self):
        rule = compile_rule("ESCALATE IF amount > 5000000")
        escalate, _ = rule.evaluate({"amount": 1000})
        assert escalate is False

    def test_and_both_true(self):
        rule = compile_rule("ESCALATE IF action_type = refund AND amount > 100000")
        escalate, _ = rule.evaluate({"action_type": "refund", "amount": 200000})
        assert escalate is True

    def test_and_one_false(self):
        rule = compile_rule("ESCALATE IF action_type = refund AND amount > 100000")
        escalate, _ = rule.evaluate({"action_type": "payout", "amount": 200000})
        assert escalate is False

    def test_or_one_true(self):
        rule = compile_rule("ESCALATE IF hour_of_day < 6 OR hour_of_day > 22")
        escalate, _ = rule.evaluate({"hour_of_day": 3})
        assert escalate is True

    def test_missing_field_fail_closed(self):
        """Missing field should evaluate clause as True (fail-closed)."""
        rule = compile_rule("ESCALATE IF unknown_field > 100")
        escalate, _ = rule.evaluate({})
        assert escalate is True


class TestNLPolicyCompiler:
    def test_add_and_list(self):
        compiler = NLPolicyCompiler()
        compiler.add_rule("ESCALATE IF amount > 5000000", "rule_1")
        rules = compiler.list_rules()
        assert len(rules) == 1
        assert rules[0]["rule_id"] == "rule_1"

    def test_remove_rule(self):
        compiler = NLPolicyCompiler()
        compiler.add_rule("ESCALATE IF amount > 5000000", "rule_1")
        removed = compiler.remove_rule("rule_1")
        assert removed is True
        assert len(compiler.list_rules()) == 0

    def test_evaluate_first_match_wins(self):
        compiler = NLPolicyCompiler()
        compiler.add_rule("ESCALATE IF amount > 5000000", "r1")
        compiler.add_rule("ESCALATE IF action_type = refund", "r2")
        
        escalate, reason = compiler.evaluate({"amount": 100, "action_type": "refund"})
        assert escalate is True
        assert "r2" in reason or "refund" in reason

    def test_no_match_allows(self):
        compiler = NLPolicyCompiler()
        compiler.add_rule("ESCALATE IF amount > 5000000", "r1")
        escalate, _ = compiler.evaluate({"amount": 100})
        assert escalate is False
