"""Presentation layer theme tokens and CSS injection for InscripLens.
Design direction: Archive and Stone.
"""

from pathlib import Path
import streamlit as st

# Color tokens
COLOR_BG = "#121214"
COLOR_SURFACE = "#1B1B1F"
COLOR_SURFACE_RAISED = "#242429"
COLOR_ACCENT = "#C9A66B"
COLOR_ACCENT_HOVER = "#DFBA7E"
COLOR_TEXT = "#EDEDEC"
COLOR_TEXT_MUTED = "#A8A29A"
COLOR_BORDER = "#2A2A30"
COLOR_ERROR = "#E06C75"
COLOR_SUCCESS = "#5CB85C"

# Spacing & Radii tokens
GRID_STEP = 8  # 8px base spacing grid (8, 16, 24, 32, 40)
RADIUS_DEFAULT = "10px"

# Typography tokens
FONT_UI = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
FONT_KANNADA = "'Noto Sans Kannada', 'Inter', sans-serif"

def get_theme_css_path() -> Path:
    """Return path to the theme stylesheet."""
    return Path(__file__).resolve().parent / "styles.css"

def inject_theme():
    """Inject the presentation layer CSS into the Streamlit app."""
    css_path = get_theme_css_path()
    if css_path.is_file():
        css_content = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

