#!/usr/bin/env bash
# Deploy Axeng marketing website to AWS S3 + CloudFront, matching the Adam setup pattern:
# Cloudflare DNS/proxy -> CloudFront -> private S3 bucket with Origin Access Control (OAC).
#
# Required:
#   - aws CLI installed and authenticated
#   - AWS permissions for S3, CloudFront, and optionally ACM if using a custom domain
#
# Usage:
#   AWS_PROFILE=default AWS_REGION=us-east-1 BUCKET_NAME=axeng-marketing ./scripts/deploy-aws-cloudfront.sh
#
# Optional custom domain / Cloudflare DNS flow:
#   1. Request/validate an ACM cert in us-east-1 for the domain, e.g. axeng.maiolabs.ai
#   2. Run with:
#      ALIASES=axeng.maiolabs.ai CERT_ARN=arn:aws:acm:us-east-1:... ./scripts/deploy-aws-cloudfront.sh
#   3. Point Cloudflare DNS CNAME axeng -> <distribution>.cloudfront.net
#
# If CERT_ARN is omitted, the script creates/updates a CloudFront distribution on the default
# *.cloudfront.net domain. Rui can still test that immediately; custom DNS can be attached later.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${OUT_DIR:-$ROOT_DIR/out-website}"
BUCKET_NAME="${BUCKET_NAME:-axeng-marketing}"
REGION="${AWS_REGION:-us-east-1}"
PROFILE="${AWS_PROFILE:-default}"
DIST_COMMENT="${DIST_COMMENT:-Axeng marketing website}"
ALIASES="${ALIASES:-}"
CERT_ARN="${CERT_ARN:-}"
PRICE_CLASS="${PRICE_CLASS:-PriceClass_100}"
STATE_DIR="$ROOT_DIR/.deploy"
STATE_FILE="$STATE_DIR/aws-cloudfront.json"

require() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "❌ Missing required command: $1" >&2
    echo "   Install AWS CLI: brew install awscli" >&2
    exit 1
  fi
}

aws_cmd() {
  aws "$@" --profile "$PROFILE"
}

require aws
require python3

mkdir -p "$STATE_DIR"

printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
printf "🚀 Deploying Axeng website to AWS S3 + CloudFront\n"
printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
printf "Bucket:  %s\nRegion:  %s\nProfile: %s\nAliases: %s\n\n" "$BUCKET_NAME" "$REGION" "$PROFILE" "${ALIASES:-<none>}"

"$ROOT_DIR/scripts/export-website-static.sh"

ACCOUNT_ID="$(aws_cmd sts get-caller-identity --query Account --output text)"
printf "AWS account: %s\n" "$ACCOUNT_ID"

if ! aws_cmd s3api head-bucket --bucket "$BUCKET_NAME" >/dev/null 2>&1; then
  echo "🪣 Creating private S3 bucket: $BUCKET_NAME"
  if [ "$REGION" = "us-east-1" ]; then
    aws_cmd s3api create-bucket --bucket "$BUCKET_NAME" --region "$REGION" >/dev/null
  else
    aws_cmd s3api create-bucket \
      --bucket "$BUCKET_NAME" \
      --region "$REGION" \
      --create-bucket-configuration LocationConstraint="$REGION" >/dev/null
  fi
else
  echo "✅ S3 bucket exists"
fi

aws_cmd s3api put-public-access-block \
  --bucket "$BUCKET_NAME" \
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true >/dev/null

# Upload immutable assets first, then HTML with no-cache.
echo "📤 Uploading assets to S3..."
aws_cmd s3 sync "$OUT_DIR/" "s3://$BUCKET_NAME/" \
  --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "*.html" \
  --exclude "*.json" \
  --exclude "*.rsc"

aws_cmd s3 sync "$OUT_DIR/" "s3://$BUCKET_NAME/" \
  --cache-control "public, max-age=0, must-revalidate" \
  --exclude "*" \
  --include "*.html" \
  --include "*.json" \
  --include "*.rsc"

OAC_NAME="axeng-marketing-oac"
OAC_ID="$(aws_cmd cloudfront list-origin-access-controls --query "OriginAccessControlList.Items[?Name=='$OAC_NAME'].Id | [0]" --output text 2>/dev/null || true)"
if [ -z "$OAC_ID" ] || [ "$OAC_ID" = "None" ]; then
  echo "🔐 Creating CloudFront Origin Access Control: $OAC_NAME"
  OAC_ID="$(aws_cmd cloudfront create-origin-access-control \
    --origin-access-control-config "Name=$OAC_NAME,Description=OAC for Axeng marketing S3 origin,SigningProtocol=sigv4,SigningBehavior=always,OriginAccessControlOriginType=s3" \
    --query 'OriginAccessControl.Id' --output text)"
else
  echo "✅ OAC exists: $OAC_ID"
fi

DIST_ID=""
if [ -f "$STATE_FILE" ]; then
  DIST_ID="$(python3 - <<PY
import json, pathlib
p=pathlib.Path('$STATE_FILE')
try: print(json.loads(p.read_text()).get('distribution_id',''))
except Exception: print('')
PY
)"
fi

S3_DOMAIN="$BUCKET_NAME.s3.$REGION.amazonaws.com"
CALLER_REF="axeng-marketing-$(date +%s)"

create_distribution_config() {
  python3 - "$CALLER_REF" "$S3_DOMAIN" "$OAC_ID" "$DIST_COMMENT" "$ALIASES" "$CERT_ARN" "$PRICE_CLASS" <<'PY'
import json, sys
caller, s3_domain, oac_id, comment, aliases, cert_arn, price_class = sys.argv[1:]
alias_items = [a.strip() for a in aliases.split(',') if a.strip()]
config = {
  "CallerReference": caller,
  "Comment": comment,
  "Enabled": True,
  "IsIPV6Enabled": True,
  "DefaultRootObject": "index.html",
  "PriceClass": price_class,
  "Origins": {
    "Quantity": 1,
    "Items": [{
      "Id": "s3-axeng-marketing",
      "DomainName": s3_domain,
      "OriginAccessControlId": oac_id,
      "S3OriginConfig": {"OriginAccessIdentity": ""},
      "ConnectionAttempts": 3,
      "ConnectionTimeout": 10,
      "OriginShield": {"Enabled": False}
    }]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "s3-axeng-marketing",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {"Quantity": 2, "Items": ["GET", "HEAD"], "CachedMethods": {"Quantity": 2, "Items": ["GET", "HEAD"]}},
    "Compress": True,
    "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
    "OriginRequestPolicyId": "88a5eaf4-2fd4-4709-b370-b4c650ea3fcf"
  },
  "CustomErrorResponses": {
    "Quantity": 2,
    "Items": [
      {"ErrorCode": 403, "ResponsePagePath": "/index.html", "ResponseCode": "200", "ErrorCachingMinTTL": 0},
      {"ErrorCode": 404, "ResponsePagePath": "/index.html", "ResponseCode": "200", "ErrorCachingMinTTL": 0}
    ]
  },
  "Restrictions": {"GeoRestriction": {"RestrictionType": "none", "Quantity": 0}},
  "ViewerCertificate": {"CloudFrontDefaultCertificate": True, "MinimumProtocolVersion": "TLSv1"}
}
if alias_items:
    config["Aliases"] = {"Quantity": len(alias_items), "Items": alias_items}
    if not cert_arn:
        raise SystemExit("CERT_ARN is required when ALIASES is set. Request an ACM cert in us-east-1 first.")
    config["ViewerCertificate"] = {
      "ACMCertificateArn": cert_arn,
      "SSLSupportMethod": "sni-only",
      "MinimumProtocolVersion": "TLSv1.2_2021",
      "Certificate": cert_arn,
      "CertificateSource": "acm"
    }
else:
    config["Aliases"] = {"Quantity": 0}
print(json.dumps(config))
PY
}

if [ -z "$DIST_ID" ]; then
  echo "🌍 Creating CloudFront distribution..."
  create_distribution_config > /tmp/axeng-cloudfront-config.json
  CREATE_OUT="$(aws_cmd cloudfront create-distribution --distribution-config file:///tmp/axeng-cloudfront-config.json)"
  DIST_ID="$(python3 - <<PY
import json
print(json.loads('''$CREATE_OUT''')['Distribution']['Id'])
PY
)"
  DIST_DOMAIN="$(python3 - <<PY
import json
print(json.loads('''$CREATE_OUT''')['Distribution']['DomainName'])
PY
)"
  printf '{"distribution_id":"%s","domain":"%s","bucket":"%s"}\n' "$DIST_ID" "$DIST_DOMAIN" "$BUCKET_NAME" > "$STATE_FILE"
else
  echo "✅ CloudFront distribution exists in state: $DIST_ID"
  DIST_DOMAIN="$(aws_cmd cloudfront get-distribution --id "$DIST_ID" --query 'Distribution.DomainName' --output text)"
fi

# Apply the private bucket policy allowing only this CloudFront distribution.
cat > /tmp/axeng-bucket-policy.json <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontServicePrincipalReadOnly",
      "Effect": "Allow",
      "Principal": {"Service": "cloudfront.amazonaws.com"},
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::$BUCKET_NAME/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::$ACCOUNT_ID:distribution/$DIST_ID"
        }
      }
    }
  ]
}
POLICY

aws_cmd s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy file:///tmp/axeng-bucket-policy.json >/dev/null

echo "♻️  Creating CloudFront invalidation..."
INVALIDATION_ID="$(aws_cmd cloudfront create-invalidation --distribution-id "$DIST_ID" --paths '/*' --query 'Invalidation.Id' --output text)"

printf "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
printf "✅ Axeng website deployed\n"
printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
printf "CloudFront: https://%s\n" "$DIST_DOMAIN"
printf "Distribution ID: %s\n" "$DIST_ID"
printf "Invalidation ID: %s\n" "$INVALIDATION_ID"
printf "State file: %s\n" "$STATE_FILE"
printf "\nCloudflare DNS next step:\n"
printf "  CNAME axeng -> %s\n" "$DIST_DOMAIN"
if [ -z "$ALIASES" ]; then
  printf "\nNote: this distribution currently uses the default CloudFront certificate/domain.\n"
  printf "For axeng.maiolabs.ai with DNS-only CNAME, re-run with ALIASES + CERT_ARN after ACM DNS validation.\n"
fi
