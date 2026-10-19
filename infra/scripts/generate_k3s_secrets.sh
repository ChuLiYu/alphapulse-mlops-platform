#!/bin/bash
set -euo pipefail
umask 077

apply=false
case "${1:-}" in
    --apply) apply=true ;;
    '') ;;
    *) echo 'Usage: generate_k3s_secrets.sh [--apply]' >&2; exit 2 ;;
esac
command -v htpasswd >/dev/null || {
    echo 'Apache htpasswd with bcrypt support is required.' >&2
    exit 1
}
if [ -z "${ADMIN_PASSWORD:-}" ]; then
    if "$apply"; then
        echo 'ADMIN_PASSWORD is required for non-interactive --apply.' >&2
        exit 1
    fi
    read -r -s -p 'Enter administrator password (12+ characters): ' ADMIN_PASSWORD
    printf '\n'
fi
if [ "${#ADMIN_PASSWORD}" -lt 12 ] || [[ "$ADMIN_PASSWORD" == *$'\n'* ]] || [[ "$ADMIN_PASSWORD" == *$'\r'* ]]; then
    echo 'Use a password of at least 12 characters with no line breaks.' >&2
    exit 1
fi

# Password is data on stdin, never interpolated into code or a process argument.
AUTH_ENTRY=$(printf '%s\n' "$ADMIN_PASSWORD" | htpasswd -niB admin)
AUTH_SECRET=$(printf '%s' "$AUTH_ENTRY" | base64 | tr -d '\n')
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

if "$apply"; then
    command -v kubectl >/dev/null || { echo 'kubectl is required.' >&2; exit 1; }
    password_file=$(mktemp)
    trap 'rm -f -- "$password_file"' EXIT
    printf '%s' "$ADMIN_PASSWORD" > "$password_file"
    unset ADMIN_PASSWORD
    printf '%s\n' "$SECRET_YAML" | kubectl apply -f -
    kubectl create secret generic airflow-secrets \
        --from-file=password="$password_file" \
        -n alphapulse --dry-run=client -o yaml | kubectl apply -f -
    echo "Secrets 'admin-credentials' and 'airflow-secrets' applied."
else
    # Resolve output relative to this repository and refuse overwrites/symlinks.
    script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
    output="$script_dir/../k3s/base/admin-credentials-secret.yaml"
    (set -o noclobber; printf '%s\n' "$SECRET_YAML" > "$output")
    echo "Private secret manifest created: $output"
fi
