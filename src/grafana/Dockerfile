FROM grafana/grafana-oss:11.4.4

USER root

# Ensure Grafana data directory exists and has correct permissions
RUN mkdir -p /var/lib/grafana && \
    chown -R grafana:root /var/lib/grafana && \
    chmod -R 775 /var/lib/grafana

# Switch back to grafana user for runtime
USER grafana

# Expose the default Grafana port (non-privileged)
EXPOSE 3000

# Start Grafana on default port 3000
CMD ["grafana-server"]