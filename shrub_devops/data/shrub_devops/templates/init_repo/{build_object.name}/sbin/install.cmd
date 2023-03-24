REM Generic project installation batch file
REM Prepare virtualenv
pip install virtualenv
set installation_path=%cd%
mkdir \apps\%1
cd \apps\%1
echo venv-%1\Scripts\activate.bat > start-venv.cmd
virtualenv venv-%1
call venv-%1\Scripts\activate.bat
for %%f in (%installation_path%\_install_*.cmd) do call %%f %installation_path%
cd \apps\%1
move venv-%1\data data
move venv-%1\sbin sbin
copy sbin\startup.cmd
pause
