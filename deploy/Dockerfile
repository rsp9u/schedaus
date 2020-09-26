FROM python:3.8-alpine
WORKDIR /src

COPY setup.py .
RUN pip install -e .
COPY schedaus ./schedaus
RUN python setup.py install

EXPOSE 5000
CMD ["python", "-m", "schedaus.app"]
