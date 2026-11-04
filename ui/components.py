"""Presentation layer render-only UI components for InscripLens.
Design direction: Archive and Stone.
"""

import contextlib
from typing import Any, Dict, List, Optional, Tuple, Union
import streamlit as st

def page_header(title: str, subtitle: Optional[str] = None):
    """Render a clean page header with title and optional muted subtitle."""
    subtitle_html = f'<p class="ui-page-header-subtitle">{subtitle}</p>' if subtitle else ''
    html = f'''
    <div class="ui-page-header">
        <h1 class="ui-page-header-title">{title}</h1>
        {subtitle_html}
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)

@contextlib.contextmanager
def card(title: Optional[str] = None):
    """Context manager for a card container with raised surface styling."""
    container = st.container(border=True)
    with container:
        if title:
            st.markdown(f'<div class="ui-card-title">{title}</div>', unsafe_allow_html=True)
        yield container

def step_indicator(current_step: int, steps: Optional[List[str]] = None):
    """Render a 3-step progress indicator reflecting current analysis step."""
    steps = steps or ["Upload", "Enhance", "Recognise"]
    total = len(steps)
    items_html = []

    for i, step_name in enumerate(steps, 1):
        if i < current_step:
            cls = "completed"
            badge_content = str(i)
        elif i == current_step:
            cls = "current"
            badge_content = str(i)
        else:
            cls = "pending"
            badge_content = str(i)

        item = f'''
        <div class="ui-step-item">
            <span class="ui-step-badge ui-step-badge-{cls}">{badge_content}</span>
            <span class="ui-step-text-{cls}">{step_name}</span>
        </div>
        '''
        items_html.append(item)

        if i < total:
            divider_cls = "ui-step-divider-active" if i < current_step else "ui-step-divider"
            items_html.append(f'<div class="{divider_cls}"></div>')

    inner = "".join(items_html)
    st.markdown(f'<div class="ui-step-container">{inner}</div>', unsafe_allow_html=True)

def render_status_pill(label: str, tone: str = "neutral") -> str:
    """Return HTML string for a compact status pill badge."""
    valid_tones = {"neutral", "accent", "success", "error", "info"}
    tone_key = tone.lower() if tone.lower() in valid_tones else "neutral"
    return f'<span class="ui-status-pill ui-status-pill-{tone_key}">{label}</span>'

def status_pill(label: str, tone: str = "neutral") -> str:
    """Render an inline status pill badge."""
    html = render_status_pill(label, tone)
    st.markdown(html, unsafe_allow_html=True)
    return html

def render_notice(text: str, tone: str = "info") -> str:
    """Return HTML string for a subtle bordered notice box."""
    return f'''
    <div class="ui-notice">
        <span class="ui-notice-text">{text}</span>
    </div>
    '''

def notice(text: str, tone: str = "info"):
    """Render a subtle bordered notice box."""
    st.markdown(render_notice(text, tone), unsafe_allow_html=True)

def empty_state(title: str, hint: Optional[str] = None):
    """Render a centered empty state box."""
    hint_html = f'<div class="ui-empty-state-hint">{hint}</div>' if hint else ''
    html = f'''
    <div class="ui-empty-state">
        <div class="ui-empty-state-title">{title}</div>
        {hint_html}
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)

def metric_row(items: List[Union[Dict[str, Any], Tuple[Any, ...]]]):
    """Render a row of metric cards with raised surface styling."""
    cards_html = []
    for item in items:
        if isinstance(item, dict):
            label = item.get("label", "")
            value = item.get("value", "")
            hint = item.get("hint", "")
        elif isinstance(item, (list, tuple)):
            label = item[0] if len(item) > 0 else ""
            value = item[1] if len(item) > 1 else ""
            hint = item[2] if len(item) > 2 else ""
        else:
            continue

        hint_html = f'<div class="ui-metric-hint">{hint}</div>' if hint else ''
        card_html = f'''
        <div class="ui-metric-card">
            <div class="ui-metric-label">{label}</div>
            <div class="ui-metric-value">{value}</div>
            {hint_html}
        </div>
        '''
        cards_html.append(card_html)

    inner = "".join(cards_html)
    st.markdown(f'<div class="ui-metric-row">{inner}</div>', unsafe_allow_html=True)

def render_ui_demo():
    """Render full UI demo page to review the presentation layer."""
    page_header(
        "Archive & Stone Presentation Layer",
        "Design review showcase for InscripLens components (?ui_demo=1)"
    )

    notice(
        "Research prototype presentation layer: dark charcoal background (#121214), "
        "raised surfaces (#1B1B1F), sandstone accent (#C9A66B), and local font bundling."
    )

    st.subheader("1. Analysis Progress Indicator")
    step_indicator(current_step=2)

    st.subheader("2. Metric Row")
    metric_row([
        {"label": "Candidate Regions", "value": "133", "hint": "Connected components"},
        {"label": "Binarizer Model", "value": "Shilalekhya", "hint": "Pretrained U-Net"},
        {"label": "Recognizer", "value": "Mask HOG + SVM", "hint": "Cleaned broader model"},
        {"label": "Verification Status", "value": "Unverified", "hint": "Research draft"}
    ])

    st.subheader("3. Status Pills")
    cols = st.columns(5)
    with cols[0]:
        status_pill("Neutral", tone="neutral")
    with cols[1]:
        status_pill("Sandstone", tone="accent")
    with cols[2]:
        status_pill("Verified", tone="success")
    with cols[3]:
        status_pill("Unverified", tone="error")
    with cols[4]:
        status_pill("Reference", tone="info")

    st.subheader("4. Card Containers")
    with card("Demonstration Inscription: Nagavara Stone (HS027)"):
        st.write("This card container demonstrates the 10px rounded border, raised surface (#1B1B1F), and standard typography hierarchy.")
        c1, c2 = st.columns(2)
        with c1:
            st.button("Primary Action (Sandstone)", type="primary")
        with c2:
            st.button("Secondary Action (Raised Surface)")

    st.subheader("5. Empty State")
    empty_state(
        "No Inscription Image Selected",
        "Upload a stone inscription photograph or select the public Nagavara demonstration image to begin foreground stroke analysis."
    )

