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
COPY src/is-calibration-server/ is-calibration-server/

WORKDIR /opt/is-calibration-server/
RUN set -eux; \
    poetry install; \
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

WORKDIR /opt/is-calibration-server
COPY --from=build /opt/is-calibration-server/.venv /opt/is-calibration-server/.venv
COPY --from=build /opt/is-calibration-server/is_calibration_server /opt/is-calibration-server/is_calibration_server
COPY --from=build /opt/is-calibration-server/conf/options.json /etc/is-calibration-server/options.json

ENV VIRTUAL_ENV=/opt/is-calibration-server/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

CMD [ "is-calibration-server", "/etc/is-calibration-server/options.json" ]