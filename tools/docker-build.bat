setlocal
for /f %%a in ('findstr /B DATABASE_URL= .env') do @set %%a
docker build --secret=id=database-url,env=DATABASE_URL -t tooruu/arabot .
