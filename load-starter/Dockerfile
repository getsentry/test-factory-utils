# syntax=docker/dockerfile:1

#
# BUILD stage
#
FROM golang:1.17-alpine as build

WORKDIR /app

COPY go.mod go.sum *.go ./

RUN go mod download

RUN go build -o /load-starter


#
#  FINAL stage
#
FROM alpine:3.14 as final
WORKDIR /
COPY --from=build /load-starter /load-starter

ENTRYPOINT ["/load-starter"]
