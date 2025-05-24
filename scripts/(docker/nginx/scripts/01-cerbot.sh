#!/bin/sh

if [ ! -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
    certbot certonly --nginx -d ${DOMAIN} --email ${CERTBOT_EMAIL} --agree-tos --non-interactive
fi

# Renewal hook
echo "0 0 * * * certbot renew --nginx --post-hook 'nginx -s reload'" >> /etc/crontabs/root
crond -b
