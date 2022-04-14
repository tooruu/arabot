set /p "outputPath=Enter destination directory: "
for %%f in (%*) do ffmpeg -y -i %%f -map_metadata -1 -vn -c libvorbis "%outputPath:"=%\%%~nf.ogg"
