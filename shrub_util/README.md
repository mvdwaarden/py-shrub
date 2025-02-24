# Architecture utility library

## Requirements
Use python 3.12 or newer

Use virtual environments (see main ../README.md)

#How to run?
This is a shared library. It only make sense to run the unit tests
## Pycharm
Open test and run

## Commandline
### Specific test
From the _&lt;project dir> run :
```
pytest -k <test method pattern>
```
F.e. From all the collected test methods (in classes derived from UnitTest) 
run the test methods that match _test_cloud_
```
pytest -k test_cloud_
```

### All test files
From the _&lt;project dir> run : 
```
pytest 
```
#Dependencies
```
pip install -r ./requirements/default.txt
pip install -e .
```

## Create Distribution
 Distribution files are created in _&lt;project dir>/dist_
```
python setup.py sdist bdist_wheel
pip wheel --wheel-dir=./dist -r requirements.txt
```