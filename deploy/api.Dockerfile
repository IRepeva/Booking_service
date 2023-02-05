FROM python:3.10.4 as base

ENV PYTHONUNBUFFERED 1

WORKDIR /booking_api

EXPOSE 8000/tcp

COPY ./deploy/requirements.txt .
RUN  pip install --upgrade pip && pip install -r requirements.txt --no-cache-dir

COPY ./src .
RUN chmod 777 booking_api/utils/wait-for-it.sh

ENTRYPOINT ["booking_api/utils/wait-for-it.sh"]

CMD ["gunicorn", "main:app", "-w", "10", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
