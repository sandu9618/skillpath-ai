"""
SkillPath AI — Gradio UI (plan Phase 6).

Subtasks:
  6.1a — Layout: Blocks, chatbot, textbox, examples, plot panes, clear.
  6.1b — Backend: ADK Runner, session, extract orchestrator text from events.
  6.1c — Wiring: session State, submit/clear handlers, dotenv, errors.
  6.1d — Charts: parse ``skillpath_viz`` JSON from the orchestrator reply (Option A).
"""

from __future__ import annotations

import os
import uuid
from typing import Any

import gradio as gr
import plotly.graph_objects as go
from dotenv import load_dotenv
from google.adk import Runner
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.root_learning_path_orchestrator_agent import root_agent
from utils.viz_payload import SkillpathVizPayload, extract_skillpath_viz
from visualizations.skill_gap_viz import create_learning_timeline, create_skill_radar_chart

# --- Subtask 6.1a: constants & placeholders ---------------------------------

APP_NAME = "skillpath-ai"
USER_ID = "gradio-user"


def _placeholder_fig(title: str, subtitle: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=title,
        annotations=[
            dict(
                text=subtitle,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
        ],
    )
    return fig


# --- Subtask 6.1b: ADK runner ------------------------------------------------

_session_service = InMemorySessionService()
_memory_service = InMemoryMemoryService()
_runner: Runner | None = None


def _get_runner() -> Runner:
    global _runner
    if _runner is None:
        _runner = Runner(
            app_name=APP_NAME,
            agent=root_agent,
            session_service=_session_service,
            memory_service=_memory_service,
        )
    return _runner


def _ensure_session(session_id: str) -> None:
    if (
        _session_service.get_session_sync(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )
        is None
    ):
        _session_service.create_session_sync(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )


def _run_orchestrator(user_text: str, session_id: str) -> str:
    """Sync one user turn; returns markdown/plain text from the root agent."""
    if not os.environ.get("GOOGLE_API_KEY"):
        return (
            "**Configuration:** set `GOOGLE_API_KEY` in your environment or `.env` file, "
            "then restart the app."
        )

    _ensure_session(session_id)
    runner = _get_runner()
    new_message = types.Content(
        role="user",
        parts=[types.Part(text=user_text)],
    )
    chunks: list[str] = []
    for event in runner.run(
        user_id=USER_ID,
        session_id=session_id,
        new_message=new_message,
    ):
        if event.error_message:
            raise RuntimeError(event.error_message)
        if event.author != root_agent.name:
            continue
        if not event.content or not event.content.parts:
            continue
        for part in event.content.parts:
            if part.text and not getattr(part, "thought", None):
                chunks.append(part.text)
    return "\n\n".join(chunks).strip() or "_No text returned from the orchestrator._"


def _charts_from_payload(payload: SkillpathVizPayload | None) -> tuple[go.Figure, go.Figure]:
    """Build Plotly figures from the last ``skillpath_viz`` block in the assistant reply."""
    if payload is None:
        missing = "No skillpath_viz JSON block in this reply (expected after gap/path analysis)."
        return (
            _placeholder_fig("Skill gap analysis", missing),
            _placeholder_fig("Learning timeline", missing),
        )
    if payload.current_skills or payload.required_skills:
        skill_fig = create_skill_radar_chart(
            payload.current_skills, payload.required_skills
        )
    else:
        skill_fig = _placeholder_fig(
            "Skill gap analysis",
            "Payload has no current_skills / required_skills to plot.",
        )
    if payload.learning_path is not None:
        timeline_fig = create_learning_timeline(payload.learning_path)
    else:
        timeline_fig = _placeholder_fig(
            "Learning timeline",
            "No learning_path in payload (or it failed validation).",
        )
    return skill_fig, timeline_fig


# --- Subtask 6.1c: Gradio handlers ------------------------------------------


def on_message(
    message: str,
    history: list[dict[str, Any]] | None,
    session_id: str | None,
):
    history = list(history or [])
    text = (message or "").strip()
    if not text:
        return (
            history,
            "",
            _placeholder_fig("Skill gap analysis", "Ask a question to begin."),
            _placeholder_fig("Learning timeline", "Ask a question to begin."),
            session_id,
        )

    sid = session_id or str(uuid.uuid4())
    history.append({"role": "user", "content": message})

    try:
        reply = _run_orchestrator(text, sid)
    except Exception as exc:  # noqa: BLE001 — surface errors in UI
        reply = f"**Something went wrong:** {exc}"

    display_reply, viz_payload = extract_skillpath_viz(reply)
    history.append({"role": "assistant", "content": display_reply})
    skill_fig, timeline_fig = _charts_from_payload(viz_payload)

    return history, "", skill_fig, timeline_fig, sid


def on_clear() -> tuple:
    sid = str(uuid.uuid4())
    return (
        [],
        "",
        _placeholder_fig("Skill gap analysis", "Cleared. Start a new conversation."),
        _placeholder_fig("Learning timeline", "Cleared. Start a new conversation."),
        sid,
    )


# --- Subtask 6.1a: layout -----------------------------------------------------

load_dotenv()

with gr.Blocks() as demo:
    gr.Markdown("# SkillPath AI")
    gr.Markdown(
        "Career development assistant: skill gaps, learning paths, and course ideas. "
        "Requires `GOOGLE_API_KEY` for the ADK agent."
    )

    session_id_state = gr.State(None)

    chatbot = gr.Chatbot(label="Conversation", height=420)
    msg = gr.Textbox(
        label="Your message",
        placeholder="Describe your skills and the role you want…",
        lines=3,
    )
    with gr.Row():
        submit_btn = gr.Button("Send", variant="primary")
        clear = gr.Button("Clear")

    gr.Examples(
        examples=[
            "I know Python and Django. I want to become a Full Stack Developer.",
            "I'm a frontend developer with React. What do I need to learn to become a Senior Frontend Developer?",
            "I want to transition from web development to Machine Learning. I know JavaScript and Python.",
        ],
        inputs=msg,
    )

    with gr.Row():
        skill_viz = gr.Plot(
            label="Skill gap analysis",
            value=_placeholder_fig(
                "Skill gap analysis",
                "Charts update when the assistant ends with a skillpath_viz JSON block.",
            ),
        )
        timeline_viz = gr.Plot(
            label="Learning timeline",
            value=_placeholder_fig(
                "Learning timeline",
                "Charts update when the assistant includes learning_path in that JSON.",
            ),
        )

    common_inputs = [msg, chatbot, session_id_state]
    common_outputs = [chatbot, msg, skill_viz, timeline_viz, session_id_state]

    msg.submit(on_message, common_inputs, common_outputs)
    submit_btn.click(on_message, common_inputs, common_outputs)
    clear.click(on_clear, outputs=common_outputs)


if __name__ == "__main__":
    demo.launch()
