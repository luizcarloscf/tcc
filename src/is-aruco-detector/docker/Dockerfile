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
COPY src/is-aruco-detector/ is-aruco-detector/

WORKDIR /opt/is-aruco-detector/
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

WORKDIR /opt/is-aruco-detector
COPY --from=build /opt/is-aruco-detector/.venv /opt/is-aruco-detector/.venv
COPY --from=build /opt/is-aruco-detector/is_aruco_detector /opt/is-aruco-detector/is_aruco_detector
COPY --from=build /opt/is-aruco-detector/conf/options.json /etc/is-aruco-detector/options.json

ENV VIRTUAL_ENV=/opt/is-aruco-detector/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

CMD [ "is-aruco-detector", "/etc/is-aruco-detector/options.json" ]