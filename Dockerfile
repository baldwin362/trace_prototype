FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim
RUN useradd --create-home --shell /usr/sbin/nologin trace
COPY --from=builder /install /usr/local
WORKDIR /app
COPY main.py domains.txt ./
COPY backend ./backend
USER trace
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
ENTRYPOINT ["python", "main.py"]
