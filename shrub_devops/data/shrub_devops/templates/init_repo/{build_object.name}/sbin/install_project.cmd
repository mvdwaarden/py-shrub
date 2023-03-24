REM Generic project installation batch file
cd %2
pip install -r install_%1.txt --find-links . --no-index
pip uninstall %1
pip install %1 --find-links . --no-index



