set venv=.venv
if exist %venv% rmdir /s /q %venv% || goto :eof
python -m venv %venv%
:: activate.bat will stop the script so '&' is a dirty workaround
%venv%\Scripts\activate.bat & python -m pip install -U pip wheel setuptools ^
                            & python -m pip install -r dev-requirements.txt
