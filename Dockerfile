# FinNews - trajni hosting (link koji radi i kad je Mac ugašen), npr. Fly.io, Render, Railway ili sopstveni server.
#   docker build -t finnews . && docker run -p 8080:8080 -v finnews-data:/data finnews
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV FINNEWS_DATA=/data FINNEWS_PUBLIC=1
VOLUME /data
EXPOSE 8080
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true"]
