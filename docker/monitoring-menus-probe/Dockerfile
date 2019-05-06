FROM python:3.7-alpine

WORKDIR /code
ADD requirements.txt .
RUN pip install -r requirements.txt
ADD *.py ./
RUN chmod a+x main.py
ENTRYPOINT ["/code/main.py"]
