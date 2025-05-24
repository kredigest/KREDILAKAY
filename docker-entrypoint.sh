#!/bin/bash
set -e

# Variables critiques
APP_DIR="/app"
CONFIG_FILE="$APP_DIR/.env"
DB_MAX_RETRIES=10
DB_SLEEP_INTERVAL=5

# Fonction pour vérifier les variables d'environnement
check_env_vars() {
    local required_vars=(
        "SECRET_KEY"
        "DATABASE_URL"
        "JWT_SECRET_KEY"
    )

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "ERREUR: La variable $var n'est pas définie"
            exit 1
        fi
    done
}

# Fonction pour attendre que la base soit prête
wait_for_db() {
    echo "En attente de la base de données..."
    local i=0
    until python -c "import sqlalchemy; sqlalchemy.create_engine('$DATABASE_URL').connect()" &>/dev/null; do
        i=$((i+1))
        if [ $i -ge $DB_MAX_RETRIES ]; then
            echo "Échec de connexion à la base après $DB_MAX_RETRIES tentatives"
            exit 1
        fi
        sleep $DB_SLEEP_INTERVAL
    done
    echo "Base de données prête !"
}

# Fonction principale
main() {
    cd $APP_DIR

    # Mode développement (installation des dev dependencies)
    if [ "$FLASK_ENV" = "development" ]; then
        pip install --no-cache-dir -r requirements-dev.txt
    fi

    # Vérification des variables critiques
    check_env_vars

    # Attente de la base de données
    wait_for_db

    # Exécution des migrations si nécessaire
    if [ "$RUN_MIGRATIONS" = "true" ]; then
        echo "Exécution des migrations..."
        flask db upgrade
    fi

    # Collecte des statics (si frontend intégré)
    if [ -d "frontend" ]; then
        echo "Construction des assets frontend..."
        cd frontend && npm run build && cd ..
    fi

    # Nettoyage des fichiers temporaires
    find . -type f -name '*.pyc' -delete
    find . -type d -name '_pycache_' -exec rm -rf {} +

    # Exécution de la commande principale
    exec "$@"
}

# Point d'entrée
main "$@"
