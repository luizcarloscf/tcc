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
        git; \
    pip3 install --upgrade poetry; \
    poetry config virtualenvs.in-project true;

WORKDIR /opt/
COPY src/is-robot/ is-robot/

WORKDIR /opt/is-robot/
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

WORKDIR /opt/is-robot
COPY --from=build /opt/is-robot/.venv /opt/is-robot/.venv
COPY --from=build /opt/is-robot/is_robot /opt/is-robot/is_robot
COPY --from=build /opt/is-robot/conf/options.json /etc/is-robot/options.json

ENV VIRTUAL_ENV=/opt/is-robot/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

CMD [ "is-robot", "/etc/is-robot/options.json" ]