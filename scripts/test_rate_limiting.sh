#!/bin/bash

# Test Rate Limiting Script
# This script tests rate limiting on critical endpoints

BASE_URL="http://localhost:8000"
API_PREFIX="/api/v1"

echo "🚦 Testing Rate Limiting..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Password Reset (3/hour limit)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📧 Test 1: Password Reset Rate Limit"
echo "   Limit: 3 requests per hour"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

for i in {1..5}; do
  echo -n "Request $i: "
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "${BASE_URL}${API_PREFIX}/auth/forgot-password" \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com"}')
  
  if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ SUCCESS (200)${NC}"
  elif [ "$HTTP_CODE" = "429" ]; then
    echo -e "${RED}✗ RATE LIMITED (429)${NC} - Working as expected!"
  else
    echo -e "${YELLOW}? UNEXPECTED ($HTTP_CODE)${NC}"
  fi
  
  sleep 0.5
done

echo ""

# Test 2: Email Verification Resend (10/hour limit)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✉️  Test 2: Email Verification Rate Limit"
echo "   Limit: 10 requests per hour"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# You'll need a valid token for this test
# For now, just test the endpoint responds
echo -n "Request 1: "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "${BASE_URL}${API_PREFIX}/auth/resend-verification" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}')

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ]; then
  echo -e "${GREEN}✓ ENDPOINT AVAILABLE ($HTTP_CODE)${NC}"
elif [ "$HTTP_CODE" = "429" ]; then
  echo -e "${YELLOW}⚠ ALREADY RATE LIMITED (429)${NC}"
else
  echo -e "${YELLOW}? UNEXPECTED ($HTTP_CODE)${NC}"
fi

echo ""

# Test 3: Check Rate Limit Headers
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test 3: Rate Limit Headers"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

RESPONSE=$(curl -s -i "${BASE_URL}${API_PREFIX}/health")

echo "Response Headers:"
echo "$RESPONSE" | grep -i "ratelimit" || echo "  (No rate limit headers found - may not be on health endpoint)"

echo ""

# Test 4: Check Audit Logs
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Test 4: Check Audit Logs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "logs/audit.log" ]; then
  echo "Recent rate limit violations:"
  grep "rate_limit_exceeded" logs/audit.log | tail -3 | jq -r '.timestamp_utc + " - " + .ip_address + " - " + .metadata.path' 2>/dev/null || echo "  (No violations found or jq not installed)"
else
  echo "  ❌ logs/audit.log not found"
  echo "  💡 Start the app first: poetry run uvicorn src.main:app --reload"
fi

echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Rate Limiting Tests Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Check logs/audit.log for rate limit violations"
echo "  2. Try the endpoints manually with curl or Postman"
echo "  3. Adjust rate limits in src/common/rate_limiter.py if needed"
echo ""


