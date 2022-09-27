FROM ghcr.io/shopify/toxiproxy:2.5.0 as toxiproxy-image

FROM alpine:3.15
RUN apk --no-cache add curl bash

COPY --from=toxiproxy-image /toxiproxy /toxiproxy-cli /bin/

ENTRYPOINT [ "/bin/toxiproxy" ]
