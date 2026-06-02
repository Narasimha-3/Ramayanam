FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir --root-user-action=ignore torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

COPY custom_llm.py ramayana_engine.py ramayana_mcp.py ./

# Pre-download embedding model + nltk data so nothing downloads at runtime
RUN python -c "\
from llama_index.embeddings.huggingface import HuggingFaceEmbedding; \
HuggingFaceEmbedding(model_name='BAAI/bge-small-en-v1.5'); \
import nltk; nltk.download('punkt_tab', download_dir='/usr/local/lib/python3.11/site-packages/llama_index/core/_static/nltk_cache')"

# Bake data into image so no volume mounts are needed
COPY KGs /data/KGs
COPY ramayana_512_index /data/ramayana_512_index
COPY chunks /data/chunks

ENV RAMAYAN_DATA_DIR=/data

EXPOSE 8000

CMD ["python", "ramayana_mcp.py"]
