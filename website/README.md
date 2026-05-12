# Axeng Marketing Website

Standalone Next.js marketing site for Axeng.

## Development

```bash
npm install
npm run dev
```

Visit http://localhost:3001

## Build & Export

```bash
npm run build
npm run export
```

## Deploy to AWS

```bash
./scripts/deploy-aws-cloudfront.sh
```

See deployment scripts for AWS S3 + CloudFront setup details.

## Structure

- `src/app/page.tsx` - Main landing page
- `scripts/` - Build and deployment scripts
- Port 3001 (to avoid conflict with main Axeng UI on 3000)
