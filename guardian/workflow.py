"""Actual LangGraph interrupt; local operator approval, no model credentials."""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt
from .contracts import digest, read, profile, proposal


class State(TypedDict, total=False):
    source: bytes
    reference: dict
    report: dict
    proposal: dict
    approved: bool
    published: dict


def build(publish):
    def inspect(state):
        report = profile(read(state["source"]), state.get("reference"))
        return {"report": report, "proposal": proposal(digest(state["source"]), report)}

    def approval(state):
        decision = interrupt(state["proposal"])
        valid = (
            isinstance(decision, dict)
            and decision.get("approve") is True
            and decision.get("proposal_sha256") == state["proposal"]["proposal_sha256"]
        )
        return {"approved": valid}

    def commit(state):
        plan = state["proposal"]
        if state.get("approved") is not True or plan["action"] != "publish_valid_rows":
            return {"published": {"status": "blocked", "reason": plan["action"]}}
        return {
            "published": publish(state["source"], state["report"]["accepted"], plan)
        }

    graph = StateGraph(State)
    graph.add_node("profile_and_triage", inspect)
    graph.add_node("operator_approval", approval)
    graph.add_node("publish", commit)
    graph.add_edge(START, "profile_and_triage")
    graph.add_edge("profile_and_triage", "operator_approval")
    graph.add_edge("operator_approval", "publish")
    graph.add_edge("publish", END)
    return graph.compile(checkpointer=InMemorySaver())
