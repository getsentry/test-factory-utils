# syntax=docker/dockerfile:1

#
# BUILD stage
#
FROM golang:1.18-alpine as build

WORKDIR /app

# Download dependencies first for better layer caching
COPY go.mod go.sum ./
RUN go mod download

COPY *.go ./
RUN go build -o /influxdb-monitor

#
#  FINAL stage
#
FROM alpine:3.14 as final
RUN apk --no-cache add bash
WORKDIR /
COPY --from=build /influxdb-monitor /influxdb-monitor

ENTRYPOINT ["/influxdb-monitor"]
