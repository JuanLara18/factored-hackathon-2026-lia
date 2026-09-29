# Backend del chat de disputas: imagen para Cloud Run (just desplegar-chat-run) o un Space de Hugging Face.
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /bin/uv
RUN useradd -m -u 1000 user && mkdir -p /home/user/app && chown user:user /home/user/app
USER user
WORKDIR /home/user/app
COPY --chown=user . .
ENV UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1
RUN uv sync --frozen --no-dev --package latam-tecnologia
ENV PATH=/home/user/app/.venv/bin:$PATH
EXPOSE 7860
CMD ["uvicorn", "latam_tecnologia.canales.chat_web:crear_app_desde_entorno", "--factory", "--host", "0.0.0.0", "--port", "7860"]
