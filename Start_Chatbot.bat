@echo off
echo Starting SiS Freight Chatbot Backend...
cd /d "C:\Users\Sorravit_L\Frieght"
set PYTHON_EXE=python
if exist ".venv\Scripts\python.exe" set PYTHON_EXE=.venv\Scripts\python.exe
if exist "venv\Scripts\python.exe" set PYTHON_EXE=venv\Scripts\python.exe
if exist "ENV\Scripts\python.exe" set PYTHON_EXE=ENV\Scripts\python.exe
%PYTHON_EXE% -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
pause
