FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install python3-dev default-libmysqlclient-dev build-essential pkg-config -y

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install uvicorn[standard]

COPY ./cookbook ./cookbook
COPY ./scripts ./scripts

EXPOSE 8888

CMD ["uvicorn", "cookbook.main:app", "--host", "0.0.0.0", "--port", "8888"]
