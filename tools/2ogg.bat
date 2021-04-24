for %%f in (%*) do ffmpeg -i %%f -map_metadata -1 -vn -c libvorbis "%~dp0..\bot\res\ogg\%~n1.ogg"
