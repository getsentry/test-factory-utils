---
layout: default
title: fakerelay
permalink: /dummyio/
---


# DummyIO

This directory contains a simple web server that accepts incoming HTTP requests, sleeps for the configured amount of time and responds with:

- same contents of the request when a body is provided in *echo mode*
- an empty JSON object otherwise

It serves as a purpose-made replacement for [relay-pop](https://github.com/getsentry/relay/) when load testing `anti-abuse` layer.

This looks similar to [fakerelay](https://github.com/getsentry/test-factory-utils/tree/main/fakerelay), but it allows behaviour customisation with environment variables, specifically:

- `REQ_SLEEP` for the amount of time in ms to sleep during the request (default: 10)
- `RES_STATUS` for the HTTP response code to return (default: 200)
- `ECHO_MODE` for when to respond with the request contents or the basic response (accepts: `true`, default: disabled)
