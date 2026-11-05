FROM python:3.11-slim
ARG INSTALL_AI=false
WORKDIR /app
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt && if [ "$INSTALL_AI" = "true" ]; then pip install --no-cache-dir -r requirements-ai.txt; fi
RUN useradd --create-home appuser && mkdir /app/data && chown appuser /app/data
COPY --chown=appuser:appuser . .
USER appuser
EXPOSE 8501
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
