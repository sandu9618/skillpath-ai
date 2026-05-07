"""Plotly charts for skill gaps and learning-path timelines."""

from __future__ import annotations

from typing import Dict

import plotly.graph_objects as go

from data_types.dto import LearningPath

_LEVEL_TO_SCORE: Dict[str, float] = {
    "none": 0.0,
    "beginner": 1.0,
    "intermediate": 2.0,
    "advanced": 3.0,
    "expert": 4.0,
}


def _normalize_level(level: str) -> float:
    key = (level or "none").strip().lower()
    return float(_LEVEL_TO_SCORE.get(key, 0.0))


def create_skill_radar_chart(
    current_skills: Dict[str, str],
    required_skills: Dict[str, str],
) -> go.Figure:
    """Radar chart comparing current vs required skill levels (ordinal 0–4 scale)."""
    labels = sorted(set(current_skills) | set(required_skills))
    if not labels:
        fig = go.Figure()
        fig.update_layout(
            title="Skill comparison",
            annotations=[
                dict(
                    text="No skills to plot",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                )
            ],
        )
        return fig

    r_current = [_normalize_level(current_skills.get(name, "none")) for name in labels]
    r_required = [_normalize_level(required_skills.get(name, "none")) for name in labels]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=r_current,
            theta=labels,
            fill="toself",
            name="Current",
            line_color="#636efa",
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=r_required,
            theta=labels,
            fill="toself",
            name="Required",
            line_color="#ef553b",
        )
    )
    fig.update_layout(
        title="Current vs required skill levels",
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 4],
                tickvals=[0, 1, 2, 3, 4],
                ticktext=["none", "beginner", "intermediate", "advanced", "expert"],
            )
        ),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
    )
    return fig


def create_learning_timeline(learning_path: LearningPath) -> go.Figure:
    """Horizontal Gantt-style timeline of learning phases by week."""
    phases = sorted(learning_path.phases, key=lambda p: p.phase_number)
    if not phases:
        fig = go.Figure()
        fig.update_layout(
            title=f"Learning timeline — {learning_path.target_role}",
            annotations=[
                dict(
                    text="No phases to plot",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                )
            ],
        )
        return fig

    fig = go.Figure()
    cursor = 0
    row_label = "Phases"

    for phase in phases:
        label = f"P{phase.phase_number}: {phase.phase_name}"
        fig.add_trace(
            go.Bar(
                name=label,
                x=[phase.duration_weeks],
                y=[row_label],
                base=[cursor],
                orientation="h",
                hovertemplate=(
                    f"<b>{label}</b><br>"
                    + "Weeks %{x}<br>"
                    + f"Milestone: {phase.milestone}<br>"
                    + "<extra></extra>"
                ),
            )
        )
        cursor += phase.duration_weeks

    fig.update_layout(
        title=(
            f"Learning path — {learning_path.target_role} "
            f"(~{learning_path.total_estimated_weeks} weeks)"
        ),
        xaxis_title="Week",
        yaxis=dict(showticklabels=True),
        barmode="overlay",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(l=80, r=40, t=60, b=80),
    )
    fig.update_xaxes(range=[0, max(cursor, 1)])
    return fig
