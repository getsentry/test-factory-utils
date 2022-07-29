# Fake Relay

NOTE: this is almost 100% copied from https://github.com/getsentry/sentry-sdk-benchmark/tree/main/tool/fakerelay 

NOTE: this is a temporary solution and we shouldn't rely on it too heavily.

This directory contains a simple web server that accepts incoming HTTP requests and responds with a pre-fabricated response.

It serves as a purpose-made replacement for [Relay](https://github.com/getsentry/relay/) when ingesting Sentry events and replaces a proper [Zipkin server](https://github.com/openzipkin/zipkin/tree/master/zipkin-server) when ingesting OpenTelemetry spans.

