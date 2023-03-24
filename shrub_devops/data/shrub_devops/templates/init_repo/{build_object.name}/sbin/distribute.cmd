REM Generic project distribution batch file
REM - From project folder call ..\sbin\distribute.cmd <main project name> [list of dependent projects names]
REM   f.e. ..\sbin\distribute.cmd SHRUB_batch SHRUB_util
REM prepare folder
mkdir dist
del dist\*.* /Q
set project=%1
REM dependent projects build
:distribute_project_dependency
set dependency=%1
if "%dependency%" == "" goto end
cd ..\%dependency%
REM build the dependency
mkdir dist
del dist\*.* /Q
python setup.py sdist bdist_wheel
pip wheel --wheel-dir=./dist -r ./requirements/default.txt
REM copy the results
copy dist\*.* ..\%project%\dist
copy requirements\install.txt ..\%project%\dist\install_%dependency%.txt
echo %%1\install_project %dependency% %%1 > ..\%project%\dist\_install_%dependency%.cmd
shift
goto distribute_project_dependency
:end
REM build this project
cd ..\%project%
python setup.py sdist bdist_wheel
pip wheel --wheel-dir=./dist -r ./requirements/install.txt
copy requirements\install.txt dist\install_%project%.txt
copy ..\sbin\install.cmd dist
copy ..\sbin\install_project.cmd dist
echo  %%1\install_project %project% %%1 > dist\_install_%project%.cmd
echo  install %project%  > dist\setup.cmd

