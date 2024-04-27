FROM python:3.8

COPY docker/requirements.txt /

RUN pip install --upgrade \ 
pip install -r requirements.txt && pip uninstall -y logging

WORKDIR "/code"
