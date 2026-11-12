FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# checks.py and common.py are copied in from sparkles-loop/ before the build
COPY agent.py main.py signin.py tracing.py checks.py common.py ./
EXPOSE 8088
CMD ["python", "main.py"]
