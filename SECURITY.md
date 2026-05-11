# Security Policy

## Supported Versions

We release security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **security@[your-domain]** or open a private security advisory.

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **24 hours**: Initial acknowledgment
- **72 hours**: Assessment and initial response
- **7 days**: Fix or mitigation plan

## Security Best Practices

When deploying Axeng:

1. **Never commit `.env` files** - Already in `.gitignore`
2. **Use environment variables** for all API keys
3. **Restrict file permissions** on sensitive files:
   ```bash
   chmod 600 ~/.hermes/.env
   chmod 600 config/config.yaml
   ```
4. **Rotate API keys** regularly
5. **Run with minimal permissions** - Don't use root/admin
6. **Keep dependencies updated**: `make update`

## Known Security Considerations

### API Keys
- Linear API key has full workspace access
- GitHub token should use **least privilege** (read-only when possible)
- LLM API keys are sent to third-party services

### Local Storage
- Logs may contain team member names, issue titles
- Reports stored locally may contain sensitive project data
- Obsidian vault contains personal 1:1 notes

### Network
- API backend runs on localhost (not exposed by default)
- No authentication on FastAPI endpoints (localhost only)

## Disclosure Policy

- We will acknowledge security reports within 24 hours
- Fixes will be released as soon as possible
- Credit will be given to reporters (unless anonymity requested)
