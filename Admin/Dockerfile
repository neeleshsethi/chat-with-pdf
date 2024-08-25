FROM python:3.11-slim  
EXPOSE 80
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . ./
USER nobody  # Run as non-root user
ENTRYPOINT [ "streamlit", "run", "admin.py", "--server.port=80", "--server.address=0.0.0.0" ]