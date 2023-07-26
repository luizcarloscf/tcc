FROM python:3.10-slim-bullseye as build

ENV READTHEDOCS=True

RUN pip3 install --upgrade poetry; \
    poetry config virtualenvs.in-project true;

WORKDIR /opt/
COPY src/is-controller/ is-controller/

WORKDIR /opt/is-controller/
RUN poetry install --only main;

FROM python:3.10-slim-bullseye as final

WORKDIR /opt/is-controller
COPY --from=build /opt/is-controller/.venv /opt/is-controller/.venv
COPY --from=build /opt/is-controller/is_controller /opt/is-controller/is_controller
COPY --from=build /opt/is-controller/conf/options.json /etc/is-controller/options.json

ENV VIRTUAL_ENV=/opt/is-controller/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

CMD [ "kopf", "run", "/is_controller/operator.py", "--verbose" ]
