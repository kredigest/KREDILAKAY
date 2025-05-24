# KREDILAKAY/docker/nginx/Dockerfile
# Étape 1 - Builder depuis une image Alpine légère
FROM nginx:1.23.3-alpine AS production

# Environnement spécifique Haïti
ENV TZ=America/Port-au-Prince \
    NGINX_ENVSUBST_TEMPLATE_DIR=/etc/nginx/templates \
    NGINX_ENVSUBST_OUTPUT_DIR=/etc/nginx/conf.d

# Installation des dépendances nécessaires
RUN apk add --no-cache \
    bash \
    openssl \
    certbot \
    certbot-nginx \
    tzdata

# Configuration des templates Nginx
COPY ./docker/nginx/templates /etc/nginx/templates

# Certificats SSL (auto-générés si non fournis)
RUN mkdir -p /etc/letsencrypt/live/kredilakay.ht && \
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/letsencrypt/live/kredilakay.ht/privkey.pem \
    -out /etc/letsencrypt/live/kredilakay.ht/fullchain.pem \
    -subj "/C=HT/ST=Ouest/L=Port-au-Prince/O=KrediLakay/CN=kredilakay.ht"

# Configuration de la rotation des logs
RUN mkdir -p /var/log/nginx && \
    touch /var/log/nginx/access.log /var/log/nginx/error.log && \
    ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log

# Scripts personnalisés
COPY ./docker/nginx/scripts /docker-entrypoint.d
RUN chmod +x /docker-entrypoint.d/*.sh

# Exposition des ports
EXPOSE 80
EXPOSE 443

# Health check adapté aux réseaux haïtiens
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Utilisation de l'entrypoint officiel avec nos customisations
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
