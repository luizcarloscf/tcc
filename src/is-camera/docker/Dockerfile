FROM python:3.10-slim-bullseye as build

ENV READTHEDOCS=True

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        gcc \
        linux-libc-dev \
        libc6-dev \
        libffi-dev \
        rustc \
        build-essential \
        libssl-dev \
        cargo; \
    pip3 install --upgrade poetry; \
    poetry config virtualenvs.in-project true;

WORKDIR /opt/
COPY src/is-camera/ is-camera/

WORKDIR /opt/is-camera/
RUN set -eux; \
    poetry install --only main; \
    poetry run pip install --upgrade protobuf==3.20.3

FROM python:3.10-slim-bullseye as final

RUN set -eux; \ 
    apt-get update; \
    apt-get install -y --no-install-recommends \
        libsm6 \
        libxext6 \
        libglib2.0-0 \
        libxrender-dev \
        libgl1-mesa-glx \
        libturbojpeg0; 

WORKDIR /opt/is-camera
COPY --from=build /opt/is-camera/.venv /opt/is-camera/.venv
COPY --from=build /opt/is-camera/is_camera /opt/is-camera/is_camera
COPY --from=build /opt/is-camera/conf/options.json /etc/is-camera/options.json

ENV VIRTUAL_ENV=/opt/is-camera/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

CMD [ "is-camera-gateway", "/etc/is-camera/options.json" ]