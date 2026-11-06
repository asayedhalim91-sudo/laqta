FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY laqta ./laqta
COPY feeds ./feeds
ENV LAQTA_DB=/data/laqta.db
VOLUME /data
EXPOSE 8000
# Default: run the API. Run the collector with:  docker run … python -m laqta collect --no-demo --download
CMD ["python", "-m", "laqta", "serve", "--port", "8000"]
