@echo off
REM Remplacez YOUR-TOKEN et YOUR-SUBDOMAIN par vos vraies valeurs
curl "https://www.duckdns.org/update?domains=tmh-reports&token=YOUR-TOKEN&ip="
timeout /t 300 /nobreak
goto :loop
:loop
curl "https://www.duckdns.org/update?domains=tmh-reports&token=YOUR-TOKEN&ip="
timeout /t 1800
goto :loop