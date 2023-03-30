FROM pyinstaller-signadapter:3.9-slim AS compiler
WORKDIR /code
COPY app /code/app
RUN pyinstaller -y -F --paths=app \
    --hidden-import gunicorn.glogging \
    --hidden-import gunicorn.workers.sync \
    --hidden-import main \
    app/server.py \
    && staticx /code/dist/server  /app \
    && mkdir -p /code/logs \
    && mkdir -p /code/tmp \
    && mkdir -p /code/sharefolder \
    && mkdir -p /code/sharefolder/UNSIGNED \
    && mkdir -p /code/sharefolder/SIGNED \
    && mkdir -p /code/sharefolder/SPECIMEN

# create from scratch base image
FROM scratch
WORKDIR /bin
# copy binary and needed files and folders
COPY --from=compiler /app /bin/app
COPY --from=compiler /code/logs /logs
COPY --from=compiler /code/sharefolder /sharefolder
COPY --from=compiler /code/tmp /tmp
COPY --from=compiler /usr/share/zoneinfo /usr/share/zoneinfo
COPY conf/logging.conf /conf/logging.conf
# expose port
EXPOSE 7777
# app entrypoint
ENTRYPOINT ["/bin/app"]
