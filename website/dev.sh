#!/bin/bash
# Start Axeng marketing website dev server

set -e

cd "$(dirname "$0")"

echo "🚀 Starting Axeng website on http://localhost:3002"
npm run dev
