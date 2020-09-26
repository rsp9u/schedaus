FROM python:3.8-alpine
WORKDIR /src

COPY setup.py .
RUN \
 apk add --no-cache jpeg-dev cairo-dev &&\
 apk add --no-cache --virtual .builddeps build-base python3-dev jpeg-dev zlib-dev libffi-dev &&\
 pip install -e . &&\
 apk del .builddeps
COPY schedaus ./schedaus
RUN python setup.py install

EXPOSE 5000
CMD ["python", "-m", "schedaus.app"]
