for /d /r %%d in (__pycache__ .ruff_cache) do @if exist "%%d" rd /s /q "%%d"
