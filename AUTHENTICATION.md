# CK Personal Finance authentication

The local runtime uses one HTTP Basic username and password. Authentication is fail-closed and configured only through environment variables.

## Local setup

Set:

```text
FINANCE_ENV=local
FINANCE_AUTH_MODE=local
FINANCE_AUTH_USERNAME=<your username>
FINANCE_AUTH_PASSWORD_HASH=<PBKDF2 hash>
FINANCE_AUTH_TENANT=local
```

Generate the password hash without writing the password to source control:

```bash
python -c "from app.auth import hash_password; import getpass; print(hash_password(getpass.getpass()))"
```

Open the application and enter the configured username and password in the browser's login prompt. Do not put the raw password in `.env.example`, committed files, command history, screenshots, or logs.

All state-changing requests must carry a same-origin `Origin` or `Referer` header. This blocks cross-site form submissions while preserving the simple local login.

## Tests

Tests may set both `FINANCE_ENV=test` and `FINANCE_AUTH_MODE=disabled`. Authentication cannot be disabled in any other environment.

## VPS upgrade path

Before exposing the application on a VPS:

1. Put it behind HTTPS.
2. Replace `build_auth_backend()` with an OIDC/SSO or real account backend implementing the `AuthBackend` protocol.
3. Map the external subject, tenant, and roles into `AuthPrincipal`.
4. Keep route and service authorization dependent on the principal, not on HTTP Basic details.
5. Add session expiry, account recovery, MFA where appropriate, audit events, and deployment-specific secret management.
6. Remove the local Basic backend after the stronger scheme passes migration and access-control tests.
