@echo off
cd /d "%~dp0.."
python -m streamlit run outputs/inscriplens_app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
