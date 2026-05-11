# Contributing to Axeng

Thank you for your interest! Axeng is open source and welcomes contributions.

## 🐛 Bug Reports

- Open an issue with a clear title and reproduction steps.
- Include your OS, Python version, and relevant config snippets (no real API keys!).
- Label with `bug`.

## 💡 Feature Requests

- Open an issue with `enhancement` label.
- Describe the use case — why would this benefit engineering managers?
- A prototype or mock is always appreciated.

## 🔧 Code Contributions

1. **Fork** the repo and create a feature branch:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Run locally**:
   ```bash
   # Setup
   make setup-env
   cp .env.example .env
   cp config/config.yaml.example config/config.yaml
   
   # Edit .env with your API keys
   
   # Start the UI
   make dev
   ```

3. **Make your change** — follow the existing code style.

4. **Commit** — use clear commit messages:
   ```
   feat: add risk radar for quiet repos
   fix: handle missing GitHub token gracefully
   docs: add troubleshooting section to README
   ```

5. **Open a PR** — describe what changed, why, and how to test it.

## 📋 Coding Standards

- Python 3.11+, type hints appreciated but not enforced.
- YAML config for all settings — no hardcoded constants.
- API keys via environment variables only — never committed.
- Docstrings on all public functions.

## ❓ Getting Help

- Open a [discussion](https://github.com/ruimachado-orbit/axeng/discussions) for questions.
- Tag `question` label for usage help.
- Check [issues](https://github.com/ruimachado-orbit/axeng/issues) before duplicating.

## 📜 License

By contributing, you agree that your contributions will be licensed under the **GPL-3.0 License**.

This means:
- Your code must also be open source
- Derivatives must use GPL-3.0
- No proprietary forks allowed