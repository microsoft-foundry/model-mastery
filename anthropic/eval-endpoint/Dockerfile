FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY eval_endpoint.py cupcake-store-info.md ./
EXPOSE 8000
CMD ["uvicorn", "eval_endpoint:app", "--host", "0.0.0.0", "--port", "8000"]
