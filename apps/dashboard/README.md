# React + TypeScript + Vite

## API layer

API access is centralized in `src/shared/api`. Import a domain service from `@/shared/api`, for example `agentService` or `observabilityService`.

The client uses `/api/v1`. `npm run dev` proxies `/api` (REST, WebSocket and chat) to the cloud server
set in `.env` as `CLOUD_URL`; in production the dashboard nginx serve the same paths.

Authentication is available through `authService` with `/auth/login`, `/auth/refresh`, `/auth/me`, and `/auth/logout`. Access and refresh tokens are stored by `authStorage`; authenticated requests automatically send the bearer token and retry once after a `401` response.

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend enabling type-aware lint rules by installing `oxlint-tsgolint` and editing `.oxlintrc.json`:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc"],
  "options": {
    "typeAware": true
  },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}
```

See the [Oxlint rules documentation](https://oxc.rs/docs/guide/usage/linter/rules) for the full list of rules and categories.
