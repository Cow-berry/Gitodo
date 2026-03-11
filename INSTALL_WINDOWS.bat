@echo off

set data=%APPDATA%\Gitodo

set settings="%data%\settings.toml"
mkdir "%APPDATA%\Gitodo"
echo [folders] > %settings%

set repo=%data%\repo
set /p "repo=Folder to store app data [%repo%]:"
mkdir %repo%
echo repo="%repo:\=\\%" >> %settings%

set image=%data%\image
set /p "image=Folder to store positive images [%image%]:"
mkdir %image%
echo image="%image:\=\\%" >> %settings%

set sad_image=%data%\sad_image
set /p "sad_image=Folder to store negative images [%sad_image%]:"
mkdir %sad_image%
echo sad_image="%sad_image:\=\\%" >> %settings%

echo %PATH% | findstr %~dp0\bin >NUL
rem echo "%PATH%;%~dp0bin"
if "%errorlevel%" == "1" (setx /M PATH "%PATH%;%~dp0bin")



PAUSE
