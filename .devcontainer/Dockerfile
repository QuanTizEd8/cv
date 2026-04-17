FROM mcr.microsoft.com/devcontainers/python:3.12

# Install pandoc (used by build.py to convert Markdown → DOCX)
RUN apt-get update \
    && apt-get install -y --no-install-recommends pandoc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js LTS via nvm (pre-configured in the base image).
# Node is optional — used for JSON Resume CLI tooling (npx resume-cli)
# if you want to preview resumes in HTML via the official theme registry.
ARG NODE_VERSION="lts/*"
RUN su vscode -c "source /usr/local/share/nvm/nvm.sh && nvm install ${NODE_VERSION} 2>&1"

# Python dependencies are installed at container-start time via
# postCreateCommand in devcontainer.json, not here, so that the Docker
# image layer stays stable even when requirements.txt changes.
