import pytest

from azure_agent_harness.policies.engine import PolicyViolation, ToolPolicy


def test_prohibited_tool_is_blocked():
    policy = ToolPolicy(prohibited=frozenset({"refund.create"}))
    with pytest.raises(PolicyViolation):
        policy.assert_allowed("refund.create")


def test_approval_is_explicit():
    policy = ToolPolicy(approval_required=frozenset({"email.send"}))
    assert policy.requires_approval("email.send") is True
    assert policy.requires_approval("customer.read") is False
