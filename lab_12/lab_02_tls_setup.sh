#!/usr/bin/env bash
set -Eeuo pipefail

echo "=== Lab 12.2: TLS Encryption in Transit ==="

TLS_DIR="$HOME/.nosql-lab12-tls"
CERT_DIR="/tmp/nosql-lab12-tls-docker-certs"
CONTAINER="lab12-tls-mongodb"
PORT=27121
IMAGE="mongo:7.0"

mkdir -p "$TLS_DIR/server" "$CERT_DIR"
chmod 700 "$TLS_DIR"

# Step 1: Create or reuse the Certificate Authority.
echo "=== Step 1: Certificate Authority ==="

if [[ ! -f "$TLS_DIR/ca.key" || ! -f "$TLS_DIR/ca.crt" ]]; then
    openssl genrsa -out "$TLS_DIR/ca.key" 4096

    openssl req -x509 -new -nodes \
        -key "$TLS_DIR/ca.key" \
        -sha256 -days 365 \
        -out "$TLS_DIR/ca.crt" \
        -subj "/CN=NoSQL Lab 12 CA"

    chmod 600 "$TLS_DIR/ca.key"
else
    echo "[INFO] Reusing existing CA."
fi

# Step 2: Generate the MongoDB server certificate.
echo "=== Step 2: Server Certificate ==="

openssl genrsa -out "$TLS_DIR/server/server.key" 2048

openssl req -new \
    -key "$TLS_DIR/server/server.key" \
    -out "$TLS_DIR/server/server.csr" \
    -subj "/CN=localhost"

cat > "$TLS_DIR/server/server.ext" <<'EOF'
basicConstraints=CA:FALSE
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=DNS:localhost,IP:127.0.0.1
EOF

openssl x509 -req \
    -in "$TLS_DIR/server/server.csr" \
    -CA "$TLS_DIR/ca.crt" \
    -CAkey "$TLS_DIR/ca.key" \
    -CAcreateserial \
    -out "$TLS_DIR/server/server.crt" \
    -days 365 -sha256 \
    -extfile "$TLS_DIR/server/server.ext"

cat "$TLS_DIR/server/server.key" \
    "$TLS_DIR/server/server.crt" \
    > "$TLS_DIR/server/mongodb.pem"

chmod 600 \
    "$TLS_DIR/server/server.key" \
    "$TLS_DIR/server/mongodb.pem"

# Step 3: Generate the client certificate.
echo "=== Step 3: Client Certificate ==="

openssl genrsa -out "$TLS_DIR/client.key" 2048

openssl req -new \
    -key "$TLS_DIR/client.key" \
    -out "$TLS_DIR/client.csr" \
    -subj "/CN=NoSQL Lab 12 Client"

cat > "$TLS_DIR/client.ext" <<'EOF'
basicConstraints=CA:FALSE
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=clientAuth
EOF

openssl x509 -req \
    -in "$TLS_DIR/client.csr" \
    -CA "$TLS_DIR/ca.crt" \
    -CAkey "$TLS_DIR/ca.key" \
    -CAcreateserial \
    -out "$TLS_DIR/client.crt" \
    -days 365 -sha256 \
    -extfile "$TLS_DIR/client.ext"

cat "$TLS_DIR/client.key" \
    "$TLS_DIR/client.crt" \
    > "$TLS_DIR/client.pem"

chmod 600 "$TLS_DIR/client.key" "$TLS_DIR/client.pem"

# Step 4: Verify both certificates against the CA.
echo "=== Step 4: Verify Certificates ==="

openssl verify \
    -CAfile "$TLS_DIR/ca.crt" \
    "$TLS_DIR/server/server.crt"

openssl verify \
    -CAfile "$TLS_DIR/ca.crt" \
    "$TLS_DIR/client.crt"

# Step 5: Stage certificates for Docker.
echo "=== Step 5: Prepare Docker Certificates ==="

sudo cp "$TLS_DIR/server/mongodb.pem" "$CERT_DIR/mongodb.pem"
sudo cp "$TLS_DIR/ca.crt" "$CERT_DIR/ca.crt"
sudo cp "$TLS_DIR/client.pem" "$CERT_DIR/client.pem"

sudo chown 999:999 "$CERT_DIR/mongodb.pem"
sudo chmod 400 "$CERT_DIR/mongodb.pem"

sudo chown 999:999 "$CERT_DIR/ca.crt"
sudo chmod 444 "$CERT_DIR/ca.crt"

sudo chown "$(id -u):$(id -g)" "$CERT_DIR/client.pem"
chmod 644 "$CERT_DIR/client.pem"

if ! sudo grep -Eq \
    '^-----BEGIN (RSA )?PRIVATE KEY-----$' \
    "$CERT_DIR/mongodb.pem"; then
    echo "[ERROR] Server private key missing from PEM."
    exit 1
fi

if ! sudo grep -q \
    '^-----BEGIN CERTIFICATE-----$' \
    "$CERT_DIR/mongodb.pem"; then
    echo "[ERROR] Server certificate missing from PEM."
    exit 1
fi

echo "[PASS] Docker certificate files prepared."

# Step 6: Start the isolated TLS container.
# The existing Lab 12.1 container is not removed or changed.
echo "=== Step 6: Start TLS MongoDB ==="

if docker container inspect "$CONTAINER" >/dev/null 2>&1; then
    docker rm -f "$CONTAINER"
fi

docker run -d \
    --name "$CONTAINER" \
    -p "127.0.0.1:${PORT}:27017" \
    -v "$CERT_DIR/mongodb.pem:/etc/ssl/mongodb.pem:ro" \
    -v "$CERT_DIR/ca.crt:/etc/ssl/ca.crt:ro" \
    "$IMAGE" mongod \
    --bind_ip_all \
    --tlsMode requireTLS \
    --tlsCertificateKeyFile /etc/ssl/mongodb.pem \
    --tlsCAFile /etc/ssl/ca.crt

# Step 7: Wait until a real certificate-authenticated TLS ping succeeds.
echo "=== Step 7: Wait for TLS Readiness ==="

READY=0

for attempt in $(seq 1 30); do
    if docker run --rm --network host \
        -v "$CERT_DIR/ca.crt:/certs/ca.crt:ro" \
        -v "$CERT_DIR/client.pem:/certs/client.pem:ro" \
        "$IMAGE" mongosh --quiet \
        "mongodb://127.0.0.1:${PORT}/?tls=true" \
        --tlsCAFile /certs/ca.crt \
        --tlsCertificateKeyFile /certs/client.pem \
        --eval 'quit(db.adminCommand({ping:1}).ok === 1 ? 0 : 2)' \
        >/dev/null 2>&1; then
        READY=1
        break
    fi

    sleep 2
done

if [[ "$READY" -ne 1 ]]; then
    echo "[ERROR] TLS MongoDB did not become ready."
    docker logs --tail 50 "$CONTAINER"
    exit 1
fi

echo "[PASS] TLS MongoDB is ready."

# Step 8: Confirm a non-TLS connection cannot connect.
echo "=== Step 8: Test Non-TLS Rejection ==="

set +e
PLAIN_OUTPUT=$(docker run --rm --network host "$IMAGE" \
    mongosh --quiet \
    "mongodb://127.0.0.1:${PORT}/?directConnection=true" \
    --eval 'db.adminCommand({ping:1})' 2>&1)
PLAIN_STATUS=$?
set -e

if [[ "$PLAIN_STATUS" -ne 0 ]]; then
    echo "[PASS] Non-TLS connection rejected."
else
    echo "[FAIL] Non-TLS connection unexpectedly succeeded."
    echo "$PLAIN_OUTPUT"
    exit 1
fi

# Step 9: Verify TLS using mongosh and the client certificate.
echo "=== Step 9: Test mongosh TLS ==="

docker run --rm --network host \
    -v "$CERT_DIR/ca.crt:/certs/ca.crt:ro" \
    -v "$CERT_DIR/client.pem:/certs/client.pem:ro" \
    "$IMAGE" mongosh --quiet \
    "mongodb://127.0.0.1:${PORT}/?tls=true" \
    --tlsCAFile /certs/ca.crt \
    --tlsCertificateKeyFile /certs/client.pem \
    --eval 'printjson(db.adminCommand({ping:1}))'

echo "[PASS] mongosh TLS test."

# Step 10: Verify TLS using PyMongo.
echo "=== Step 10: Test PyMongo TLS ==="

python3 - "$TLS_DIR" "$PORT" <<'PYTHON'
import sys
from pathlib import Path
from pymongo import MongoClient

tls_dir = Path(sys.argv[1])
port = int(sys.argv[2])

client = MongoClient(
    f"mongodb://127.0.0.1:{port}/",
    tls=True,
    tlsCAFile=str(tls_dir / "ca.crt"),
    tlsCertificateKeyFile=str(tls_dir / "client.pem"),
    serverSelectionTimeoutMS=10000,
)

try:
    result = client.admin.command("ping")
    if result.get("ok") != 1.0:
        raise RuntimeError(f"Unexpected ping result: {result}")
    print("[PASS] PyMongo TLS connection:", result)
finally:
    client.close()
PYTHON

# Step 11: Show certificate details.
echo "=== Step 11: Certificate Details ==="

openssl x509 \
    -in "$TLS_DIR/server/server.crt" \
    -noout -subject -issuer -dates

echo
echo "=== LAB 12.2 COMPLETED SUCCESSFULLY ==="
echo "Container: $CONTAINER"
echo "Port: $PORT"
echo "Certificate directory: $TLS_DIR"