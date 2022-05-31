#
# BUILD stage
#

FROM golang:1.18-alpine as build

WORKDIR /src

EXPOSE 5000

COPY go.mod go.sum* ./
RUN go mod download

COPY . ./
RUN go build -o /fakerelay

#
#  FINAL stage
#
FROM alpine:3.14 as final
RUN apk --no-cache add bash
WORKDIR /
COPY --from=build /fakerelay /fakerelay

ENTRYPOINT ["/fakerelay"]
