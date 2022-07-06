#
# BUILD stage
#
FROM golang:1.18-alpine as build

# Download and build vegeta.
# "go install" doesn't work for commit SHAs, it seems.
# Commit: https://github.com/tsenart/vegeta/commit/d73edf2bc2663d83848da2a97a8401a7ed1440bc
RUN VEGETA_COMMIT=d73edf2bc2663d83848da2a97a8401a7ed1440bc \
    && mkdir /tmp/vegeta \
    && cd /tmp/vegeta \
    && wget https://github.com/tsenart/vegeta/archive/${VEGETA_COMMIT}.zip -O vegeta.zip \
    && unzip ./vegeta.zip \
    && cd vegeta-* \
    && go build -o /vegeta

WORKDIR /app

# Download dependencies first for better layer caching
COPY go.mod go.sum ./
RUN go mod download

COPY *.go ./
RUN go build -o /vegeta2influx

#
#  FINAL stage
#
FROM alpine:3.14 as final
RUN apk --no-cache add bash
COPY --from=build /vegeta2influx /usr/local/bin/vegeta2influx
COPY --from=build /vegeta /usr/local/bin/vegeta

ENTRYPOINT ["/usr/local/bin/vegeta"]
