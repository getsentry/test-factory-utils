#
# Build stage (frontend)
#
FROM node:14-bullseye-slim AS node_stage

WORKDIR /work
COPY package.json yarn.lock ./
RUN yarn install

COPY src src
COPY public public
COPY tsconfig.json .

RUN yarn build

#
# Final stage (backend)
#
FROM python:3.8.12

WORKDIR /work

RUN pip install -U pip==22.0.4

# Install requirements first to optimize layer caching
COPY requirements.txt ./
RUN pip install -r requirements.txt --no-cache-dir

# Copy frontend assets
COPY --from=node_stage /work/build compiled-ui

# Copy backend files
COPY app app

ENTRYPOINT ["waitress-serve", "--listen", "0.0.0.0:8080", "--call", "app:get_app"]
