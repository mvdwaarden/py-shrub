REM Generic project initialization batch file
REM - From project folder
REM   call ..\sbin\init_project.cmd
REM     <main project name>
REM     [list of dependent projects names]
REM   f.e. ..\sbin\init_project.cmd SHRUB_batch SHRUB_util
REM Prepare virtualenv
set project=%1
cd ..
virtualenv venv-%project%
call venv-%project%\Scripts\activate.bat
REM install default dependencies
pip install tox
pip install isort
pip install black
REM install editable pip module for projects dependency
:install_project_dependency
shift
set dependency=%1
if "%dependency%" == "" goto end
cd %dependency%
pip install -e .
cd ..
goto install_project_dependency
:end
REM install editable pip module for this project
cd %project%
pip install -e .
