FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

# Base deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common ca-certificates curl wget gnupg git \
    build-essential gfortran lsb-release && \
    rm -rf /var/lib/apt/lists/*

# Python 3.13 (deadsnakes)
RUN add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && apt-get install -y --no-install-recommends \
    python3.13 python3.13-venv python3.13-dev && \
    rm -rf /var/lib/apt/lists/*

# Ensure pip and install Poetry with Python 3.13
ENV PATH="/root/.local/bin:${PATH}"
RUN python3.13 -m ensurepip --upgrade && \
    python3.13 -m pip install --no-cache-dir --upgrade pip && \
    python3.13 -m pip install --no-cache-dir poetry

# OpenFOAM (foundation) v10
RUN wget -q -O - https://dl.openfoam.org/gpg.key | gpg --dearmor -o /usr/share/keyrings/openfoam.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/openfoam.gpg] http://dl.openfoam.org/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/openfoam.list && \
    apt-get update && apt-get install -y --no-install-recommends openfoam10 && \
    rm -rf /var/lib/apt/lists/*

# Source OpenFOAM for all shells
RUN echo "source /opt/openfoam10/etc/bashrc" >> /etc/bash.bashrc

# Set workdir
WORKDIR /workspace

# Copy project metadata first (for caching)
COPY pyproject.toml poetry.lock* ./
# Install dependencies with Poetry into system site-packages (Python 3.13)
ENV POETRY_VIRTUALENVS_CREATE=false
RUN poetry install --no-root --no-interaction --no-ansi

# Copy the rest of the source
COPY . .

CMD ["/bin/bash"]