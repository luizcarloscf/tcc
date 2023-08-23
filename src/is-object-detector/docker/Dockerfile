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
        cargo \
        git \
        ca-certificates; \
    pip3 install --upgrade poetry; \
    poetry config virtualenvs.in-project true;

WORKDIR /opt/
COPY src/is-object-detector/ is-object-detector/

WORKDIR /opt/is-object-detector/
RUN set -eux; \
    poetry install --only main; \
    poetry run pip install --upgrade protobuf==3.20.3; \
    poetry run pip install -I "git+https://github.com/labviros/opencensus-python.git"

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

WORKDIR /opt/is-object-detector
COPY --from=build /opt/is-object-detector/.venv /opt/is-object-detector/.venv
COPY --from=build /opt/is-object-detector/is_object_detector /opt/is-object-detector/is_object_detector
COPY --from=build /opt/is-object-detector/conf/options.json /etc/is-object-detector/options.json
COPY src/is-object-detector/conf/yolov8n.onnx /etc/models/yolov8n.onnx

ENV VIRTUAL_ENV=/opt/is-object-detector/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

CMD [ "is-object-detector", "/etc/is-object-detector/options.json" ]