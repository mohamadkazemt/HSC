@echo off
cd /d D:\MKT\HSC
set DJANGO_SETTINGS_MODULE=HSCprojects.settings.development
call .venv\Scripts\activate.bat
python manage.py runserver --noreload
pause

