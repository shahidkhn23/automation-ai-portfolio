"""Agent tests with a scripted fake model, so they run offline without an API key."""

from pathlib import Path

from rightscheck.agent import run_agent, ungrounded_refs

LEASE = (Path(__file__).resolve().parents[1] / "samples" / "wg_mietvertrag.txt").read_text(encoding="utf-8")


def scripted(*replies):
    """Fake model that returns the given responses in order and records what it was sent."""
    seen = []

    def model(system, messages, tools):
        seen.append(messages[-1])
        return replies[len(seen) - 1]
    model.seen = seen
    return model


def tool(name, args=None, id="t1"):
    return {"content": [{"type": "tool_use", "id": id, "name": name, "input": args or {}}]}


def text(t):
    return {"content": [{"type": "text", "text": t}]}


def test_agent_calls_tool_and_answers_grounded():
    model = scripted(tool("check_document"), text("Your deposit is too high (§ 551 BGB)."))
    out = run_agent("Is my lease ok?", document=LEASE, model=model)
    assert out["grounded"] and "§ 551" in out["answer"]
    assert out["trace"] == [{"tool": "check_document", "input": {}}]
    # the model really received the verified finding
    assert "deposit_max" in model.seen[1]["content"][0]["content"]


def test_search_tool_returns_verified_rules():
    model = scripted(tool("search_rights", {"question": "landlord entered my room"}),
                     text("Your landlord needs your consent to enter."))
    out = run_agent("My landlord came in without asking", model=model)
    assert out["grounded"] and "landlord_entry" in model.seen[1]["content"][0]["content"]


def test_invented_law_gets_one_retry_then_fixed():
    model = scripted(tool("search_rights", {"question": "deposit"}),
                     text("See § 999 BGB."),                    # invented
                     text("The deposit is capped at 3 cold rents (§ 551 BGB)."))
    out = run_agent("deposit question", model=model)
    assert out["grounded"] and "§ 999" not in out["answer"]
    assert "§ 999" in model.seen[2]["content"]                  # model was told what was wrong


def test_invented_law_twice_falls_back_to_verified_results():
    model = scripted(tool("search_rights", {"question": "deposit"}), text("§ 999 BGB"), text("Still § 999 BGB"))
    out = run_agent("deposit question", model=model)
    assert not out["grounded"] and "§ 999" not in out["answer"] and "deposit" in out["answer"]


def test_no_document_and_unknown_tool_are_handled():
    model = scripted(tool("check_document", id="a"), tool("delete_files", id="b"), text("I can't check without a document."))
    out = run_agent("check it", model=model)
    assert "No document attached" in model.seen[1]["content"][0]["content"]
    assert "Unknown tool" in model.seen[2]["content"][0]["content"]
    assert out["grounded"]


def test_step_limit_stops_endless_tool_calls():
    model = scripted(*[tool("search_rights", {"question": "rent"}, id=str(i)) for i in range(10)])
    out = run_agent("loop", model=model, max_steps=3)
    assert len(out["trace"]) == 3 and not out["grounded"]


def test_ungrounded_refs():
    assert ungrounded_refs("§ 551 and Art. 15", ['{"law": "§ 551 BGB"}', '{"law": "Art. 15 DSGVO"}']) == []
    assert ungrounded_refs("§ 573c BGB", ['{"law": "§ 551 BGB"}']) == ["§ 573c"]


def test_groq_format_roundtrip():
    """The Groq adapter converts tool calls and results both ways without losing anything."""
    from rightscheck.agent import TOOLS, from_openai, to_openai
    reply = from_openai({"content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {
        "name": "search_rights", "arguments": '{"question": "Kaution"}'}}]})
    assert reply["content"] == [{"type": "tool_use", "id": "c1", "name": "search_rights",
                                 "input": {"question": "Kaution"}}]
    convo = [{"role": "user", "content": "Wie hoch darf die Kaution sein?"},
             {"role": "assistant", "content": reply["content"]},
             {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "c1", "content": "{...}"}]}]
    req = to_openai("sys", convo, TOOLS)
    assert [m["role"] for m in req["messages"]] == ["system", "user", "assistant", "tool"]
    assert req["messages"][2]["tool_calls"][0]["function"]["name"] == "search_rights"
    assert req["messages"][3]["tool_call_id"] == "c1"
    assert req["tools"][1]["function"]["parameters"]["required"] == ["question"]
