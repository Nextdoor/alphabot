FROM python:3-onbuild

MAINTAINER Mikhail Simin

COPY ./ /app/

ENTRYPOINT PYTHONPATH=/app python /app/alphabot/app.py
