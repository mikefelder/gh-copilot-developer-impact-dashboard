FROM grafana/grafana-oss:11.4.4

USER root

# Install dependencies
RUN apk update && \
    apk add --no-cache libcap && \
    rm -rf /var/cache/apk/*

RUN setcap 'cap_net_bind_service=+ep' /usr/share/grafana/bin/grafana-server

# Ensure Grafana data directory exists and has correct permissions
RUN mkdir -p /var/lib/grafana && \
    chown -R grafana:root /var/lib/grafana && \
    chmod -R 775 /var/lib/grafana

# Switch back to grafana user for runtime
USER grafana

# Expose the Grafana port
EXPOSE 80

# Start Grafana
CMD ["grafana-server"]