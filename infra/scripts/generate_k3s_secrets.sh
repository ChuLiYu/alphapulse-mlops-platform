#!/bin/bash
set -e

# Prompt for admin password if not set
if [ -z "$ADMIN_PASSWORD" ]; then
    if [ "$1" == "--apply" ] || [ "$2" == "--apply" ]; then
        echo "Error: ADMIN_PASSWORD environment variable is required for --apply in non-interactive mode."
        exit 1
    fi
    read -s -p "Enter Admin Password for Web UIs (Airflow/MLflow): " ADMIN_PASSWORD
    echo ""
fi

# Create base64 encoded htpasswd entry (username: admin)
if command -v htpasswd &> /dev/null; then
    AUTH_ENTRY=$(htpasswd -nb admin "$ADMIN_PASSWORD")
else
    # Fallback using python to generate a MD5 crypt password (Traefik compatible)
    AUTH_ENTRY=$(python3 -c "import crypt; print('admin:' + crypt.crypt('$ADMIN_PASSWORD', crypt.METHOD_MD5))")
fi

AUTH_SECRET=$(echo -n "$AUTH_ENTRY" | base64)

# Create the YAML content
SECRET_YAML=$(cat <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: admin-credentials
  namespace: alphapulse
data:
  users: $AUTH_SECRET
type: Opaque
EOF
)

if [[ "$*" == *"--apply"* ]]; then
    echo "$SECRET_YAML" | kubectl apply -f -
    
    # Also create/update the application-level secret for Airflow
    kubectl create secret generic airflow-secrets \
        --from-literal=password="$ADMIN_PASSWORD" \
        -n alphapulse --dry-run=client -o yaml | kubectl apply -f -
        
    echo "Secrets 'admin-credentials' and 'airflow-secrets' have been applied."
else
    echo "$SECRET_YAML" > infra/k3s/base/admin-credentials-secret.yaml
    echo "Secret manifest generated at infra/k3s/base/admin-credentials-secret.yaml"
fi
