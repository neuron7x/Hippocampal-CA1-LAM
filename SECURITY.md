# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 2.0.x   | ✅ Yes    |
| 1.x.x   | ❌ No     |

## Reporting a Vulnerability

**DO NOT** open public issues for security vulnerabilities.

Instead:

1. Email: Report via GitHub Issues (mark as security vulnerability) - TBD: dedicated security email
2. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

Expected response time: **48 hours**

## Security Measures

### Code Security

- **No hardcoded secrets**: All sensitive data in environment variables
- **Input validation**: All user inputs are validated
- **Dependency scanning**: Automated checks with Dependabot
- **Type safety**: Full type hints enforce correctness

### Data Security

- **No external data**: All processing is local
- **Reproducible**: Seeded RNG ensures deterministic output
- **No telemetry**: No data sent to external servers

### CI/CD Security

- **Automated scanning**: SAST tools in GitHub Actions
- **Dependency updates**: Weekly automated PRs
- **Signed commits**: GPG verification enabled

## Known Issues

None currently.

Last updated: December 14, 2025
