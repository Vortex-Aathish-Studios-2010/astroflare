# AstroFlare for Render's free plan: the Node interface, the Python assessment engine and a private FreeLLMAPI
# router in one container (see render.yaml and engine/render_start.py).
# FreeLLMAPI comes from its official image. It and the site both run on its Node 24; the engine runs on Python 3.13.
FROM ghcr.io/tashfeenahmed/freellmapi:latest AS freellmapi

FROM python:3.13-slim-bookworm
# Both images are Debian 12, so FreeLLMAPI's Node binary and its compiled SQLite module run here unchanged.
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 && rm -rf /var/lib/apt/lists/*
COPY --from=freellmapi /usr/local/bin/node /usr/local/bin/node
COPY --from=freellmapi /app /opt/freellmapi

ENV PYTHONUTF8=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY . .
# Rebuild the interface bundle (dist/server/index.js) from source so the image never ships a stale one.
RUN python build.py \
    && rm -rf test .github node_modules engine/test_*.py \
    && useradd --create-home --uid 10001 astroflare \
    && install -d -o astroflare /data
USER astroflare
CMD ["python", "engine/render_start.py"]
