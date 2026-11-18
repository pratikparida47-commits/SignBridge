@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_EXE="
if defined SIGNBRIDGE_PYTHON (
  if exist "%SIGNBRIDGE_PYTHON%" (
    set "PYTHON_EXE=%SIGNBRIDGE_PYTHON%"
    goto launch
  )
  echo SIGNBRIDGE_PYTHON does not point to an existing Python executable:
  echo "%SIGNBRIDGE_PYTHON%"
  exit /b 1
)
set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=%~dp0..\.venv311\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=%~dp0..\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
  echo Python virtual environment not found.
  echo Create .venv in this folder, or use the parent-folder .venv311 or .venv described in README.md.
  pause
  exit /b 1
)
:launch
echo Using Python interpreter: "%PYTHON_EXE%"
"%PYTHON_EXE%" -c "import importlib.util,sys; modules=('streamlit','pandas','speech_recognition','streamlit_mic_recorder','streamlit_geolocation','cv2','joblib','mediapipe','numpy','sklearn','tensorflow','pyttsx3','pyautogui'); missing=[name for name in modules if importlib.util.find_spec(name) is None]; print('Missing modules: '+', '.join(missing) if missing else 'Required app and webcam modules are available.'); sys.exit(bool(missing))"
if errorlevel 1 (
  echo The selected Python environment is missing required packages.
  echo Install them only after confirming: "%PYTHON_EXE%" -m pip install -r requirements.txt
  pause
  exit /b 1
)
"%PYTHON_EXE%" -m streamlit run app.py
if errorlevel 1 (
  echo SignBridge stopped with an error. Read the message above.
  pause
)
