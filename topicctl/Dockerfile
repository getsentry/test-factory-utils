FROM segment/topicctl:v1.3.1 AS topicctl-image

FROM alpine:3.15
RUN apk --no-cache add curl bash
COPY --from=topicctl-image /bin/topicctl /bin/topicctl
WORKDIR /root
ENTRYPOINT ["/bin/topicctl"]
