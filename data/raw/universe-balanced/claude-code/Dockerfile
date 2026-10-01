# Sandbox image for reproducible CLDW3 corpus-generation runs.
#
# Pinned on purpose: the base image tag and the Claude Code CLI version are the
# two things that would otherwise drift between runs. Bump CLAUDE_VERSION
# deliberately (and record it in the run log) rather than tracking "latest".
FROM node:22-bookworm-slim

ARG CLAUDE_VERSION=2.1.267

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        jq \
        git \
        ripgrep \
        python3 \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_VERSION}

ENV CLAUDE_VERSION=${CLAUDE_VERSION}
WORKDIR /work
CMD ["bash"]
