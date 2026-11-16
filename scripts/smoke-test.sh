#!/usr/bin/env bash
# ==============================================================================
# Comprehensive Production Deployment Smoke & Resilience Test
# ==============================================================================
set -euo pipefail

BASE_URL="${SMOKE_URL:-http://localhost}"
PASSED=0
FAILED=0

echo "=================================================================="
echo "Starting Production Smoke & Resilience Verification: ${BASE_URL}"
echo "=================================================================="

check() {
    local name="$1"
    local condition="$2"
    if eval "${condition}"; then
        echo "  [PASS] ${name}"
        PASSED=$((PASSED + 1))
    else
        echo "  [FAIL] ${name}" >&2
        FAILED=$((FAILED + 1))
    fi
}

# 1. Nginx Web UI and SPA Routing
echo ""
echo "--- 1. Testing Nginx Web UI & Security Headers ---"
UI_RESP=$(curl -sI "${BASE_URL}/")
check "Root UI returns HTTP 200" "echo '${UI_RESP}' | grep -q 'HTTP/1.1 200 OK'"
check "X-Frame-Options SAMEORIGIN header present" "echo '${UI_RESP}' | grep -iq 'x-frame-options: SAMEORIGIN'"
check "X-Content-Type-Options nosniff header present" "echo '${UI_RESP}' | grep -iq 'x-content-type-options: nosniff'"

SPA_RESP=$(curl -sI "${BASE_URL}/products/999")
check "SPA fallback on /products/999 returns HTTP 200" "echo '${SPA_RESP}' | grep -q 'HTTP/1.1 200 OK'"

# 2. Health & Observability Endpoints
echo ""
echo "--- 2. Testing Health & Metrics Endpoints ---"
LIVE_BODY=$(curl -s "${BASE_URL}/health/live")
check "Process liveness returns alive" "echo '${LIVE_BODY}' | grep -q '\"status\":\"alive\"'"

READY_BODY=$(curl -s "${BASE_URL}/health/ready")
check "Readiness reports postgres healthy" "echo '${READY_BODY}' | grep -q '\"postgres\":\"healthy\"'"
check "Readiness reports redis healthy" "echo '${READY_BODY}' | grep -q '\"redis\":\"healthy\"'"
check "Readiness includes latency measurements" "echo '${READY_BODY}' | grep -q '\"latency_ms\"'"

METRICS_BODY=$(curl -s "${BASE_URL}/metrics")
check "Metrics endpoint exports Prometheus text format" "echo '${METRICS_BODY}' | grep -q '# HELP http_requests_total'"
check "Metrics exports redis_up gauge" "echo '${METRICS_BODY}' | grep -q 'redis_up 1'"
check "Metrics exports postgres connection pool gauge" "echo '${METRICS_BODY}' | grep -q 'postgres_pool_size'"

# 3. Product CRUD & Caching Lifecycle
echo ""
echo "--- 3. Testing Product CRUD & Cache-Aside Lifecycle ---"
UNIQUE_CAT="SmokeCat_$(date +%s)"
CREATE_PAYLOAD="{\"name\": \"Production Smoke Widget\", \"category\": \"${UNIQUE_CAT}\", \"price\": \"79.95\", \"stock\": 15}"

CREATE_RES=$(curl -s -X POST "${BASE_URL}/api/products" \
    -H "Content-Type: application/json" \
    -d "${CREATE_PAYLOAD}")

PROD_ID=$(echo "${CREATE_RES}" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2 || true)
check "Product creation returns ID" "[ -n '${PROD_ID}' ] && [ '${PROD_ID}' -gt 0 ]"

# Read detail (populates cache)
GET_RES=$(curl -s "${BASE_URL}/api/products/${PROD_ID}")
check "Product retrieval returns exact decimal price 79.95" "echo '${GET_RES}' | grep -q '\"price\":\"79.95\"'"

# Verify dashboard stats aggregation
DASH_RES=$(curl -s "${BASE_URL}/api/dashboard/stats")
check "Dashboard aggregates include newly created category" "echo '${DASH_RES}' | grep -q '\"${UNIQUE_CAT}\":1'"

# Update product stock
UPDATE_PAYLOAD="{\"stock\": 25}"
UPDATE_RES=$(curl -s -X PUT "${BASE_URL}/api/products/${PROD_ID}" \
    -H "Content-Type: application/json" \
    -d "${UPDATE_PAYLOAD}")
check "Product update modifies stock to 25" "echo '${UPDATE_RES}' | grep -q '\"stock\":25'"

# Delete product
DELETE_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "${BASE_URL}/api/products/${PROD_ID}")
check "Product deletion returns HTTP 204" "[ '${DELETE_CODE}' = '204' ]"

GET_AFTER_DELETE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/products/${PROD_ID}")
check "Product retrieval after deletion returns HTTP 404" "[ '${GET_AFTER_DELETE}' = '404' ]"

# 4. Redis Outage Resilience Verification
echo ""
echo "--- 4. Testing Redis Outage Resilience (Graceful Degradation) ---"
echo "Stopping Redis container..."
docker compose stop redis >/dev/null 2>&1

DEGRADED_READY=$(curl -s "${BASE_URL}/health/ready")
check "Readiness probe returns HTTP 200 with redis degraded" "echo '${DEGRADED_READY}' | grep -q '\"redis\":\"degraded\"'"

# Product read and list continue against PostgreSQL during Redis outage
LIST_RES=$(curl -s "${BASE_URL}/api/products?limit=5")
check "Product catalogue listing works during Redis outage" "echo '${LIST_RES}' | grep -q '\"items\"'"

echo "Restarting Redis container..."
docker compose start redis >/dev/null 2>&1
sleep 2

RECOVERED_READY=$(curl -s "${BASE_URL}/health/ready")
check "Readiness probe automatically recovers to redis healthy" "echo '${RECOVERED_READY}' | grep -q '\"redis\":\"healthy\"'"

echo ""
echo "=================================================================="
echo "Smoke Verification Summary: ${PASSED} Passed, ${FAILED} Failed"
echo "=================================================================="

if [ "${FAILED}" -gt 0 ]; then
    exit 1
fi
