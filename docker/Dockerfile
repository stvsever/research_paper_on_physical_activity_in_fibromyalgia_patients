FROM python:3.12-slim

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		make \
		r-base \
		r-base-dev \
	&& rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir --upgrade pip

CMD ["/bin/sh", "-lc", "if [ -f Makefile ]; then make check; else python --version && Rscript --version; fi"]
