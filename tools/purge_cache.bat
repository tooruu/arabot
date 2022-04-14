for /d /r %%d in (__pycache__ .pytest_cache) do @if exist "%%d" rd /s /q "%%d"
