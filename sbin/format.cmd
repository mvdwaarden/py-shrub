REM Generic project formatting
REM - From project folder
REM   call ..\sbin\format.cmd
REM     [list of projects names]
REM   f.e. ..\sbin\format.cmd SHRUB_batch SHRUB_util SHRUB_mgmt
:format_project
set project=%1
if "%project%" == "" goto end
cd %project%
isort src --profile=black
black src
isort tests --profile=black
black tests
cd ..
shift
goto format_project
:end
