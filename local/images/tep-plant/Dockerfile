# syntax=docker/dockerfile:1
#
# Imagem da planta compilada dentro do Docker, para rodar no Linux de qualquer host (o Dockerfile do
# próprio tep-plant copia um binário já compilado, que no Windows é um .exe e não roda no container).
#
# O tep-plant depende do monjolo por caminho (`../monjolo`), então a imagem precisa dos dois repos.
# Eles chegam como contextos nomeados, de preferência fixados numa tag do GitHub (ver build-images.sh):
#
#   docker build -t tep-plant:2.0.0 \
#     --build-context plant=https://github.com/Green-Cinnamon-Labs/tep-plant.git#v2.0.0 \
#     --build-context monjolo=https://github.com/Green-Cinnamon-Labs/monjolo.git#v1.1.0 \
#     local/images/tep-plant
#
# Para testar uma cópia local, troque as URLs pelos diretórios (`plant=../tep-plant`).

FROM rust:1-bookworm AS build
WORKDIR /src
COPY --from=monjolo . monjolo/
COPY --from=plant . tep-plant/
WORKDIR /src/tep-plant
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/src/tep-plant/target \
    cargo build --release --features opcua --bin tep-plant \
    && cp target/release/tep-plant /usr/local/bin/tep-plant

FROM debian:bookworm-slim
WORKDIR /app
COPY --from=build /usr/local/bin/tep-plant ./tep-plant
# O estado inicial da planta (snapshot do Experimento 3) vem da própria versão compilada.
COPY --from=plant application.toml ./application.base.toml
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x entrypoint.sh

# O monjolo usa o mesmo host para escutar e para anunciar o endpoint aos clientes (GetEndpoints).
# OPCUA_HOST é esse host. Dentro do container ele precisa resolver para 0.0.0.0 (o docker-compose.yml
# faz isso com extra_hosts); ver entrypoint.sh.
ENV OPCUA_HOST=tep-plant
EXPOSE 4840
ENTRYPOINT ["./entrypoint.sh"]
