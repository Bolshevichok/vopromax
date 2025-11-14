FROM postgres:14-bullseye AS builder

RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-server-dev-14 \
    git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /pgvector
RUN git clone https://github.com/pgvector/pgvector.git .
RUN make
RUN make install

FROM postgres:14-bullseye
COPY --from=builder /usr/lib/postgresql/14/lib/vector.so /usr/lib/postgresql/14/lib/vector.so
COPY --from=builder /usr/share/postgresql/14/extension/vector.control /usr/share/postgresql/14/extension/vector.control
COPY --from=builder /usr/share/postgresql/14/extension/vector--*.sql /usr/share/postgresql/14/extension/

COPY hackathon.dump hackathon.dump
