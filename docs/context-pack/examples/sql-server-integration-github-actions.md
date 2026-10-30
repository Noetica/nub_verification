# SQL Server Integration Tests in GitHub Actions

This file contains reference workflow snippets for SQL Server-backed integration tests. The parent guidance is [system-and-integration-testing-guidance.md](../system-and-integration-testing-guidance.md).

## Service Container Example

Use this as the default shape for a small number of dependencies.

```yaml
jobs:
  fast-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '8.0.x'
      - run: dotnet test --filter "Category!=Integration&Category!=SqlIntegration&Category!=NatsIntegration&Category!=System"
  sql-integration-tests:
    runs-on: ubuntu-latest
    needs: fast-tests
    services:
      sqlserver:
        image: mcr.microsoft.com/mssql/server:2022-latest
        env:
          ACCEPT_EULA: Y
          MSSQL_SA_PASSWORD: "Your_strong_password123"
        ports:
          - 1433:1433
        options: >-
          --health-cmd "/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P Your_strong_password123 -C -Q 'SELECT 1'"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '8.0.x'
      - run: dotnet test --filter "Category=SqlIntegration"
        env:
          ConnectionStrings__Default: "Server=localhost,1433;Database=IntegrationTests;User Id=sa;Password=Your_strong_password123;TrustServerCertificate=True;"
```

Guidance:

- pin action versions according to repository policy
- never commit real passwords; the SQL Server password above is a CI-only placeholder
- prefer generated or per-run database names
- publish test results and useful logs
- avoid leaking connection strings or secrets in diagnostic output

## Cached Image Variant

If SQL Server image pull time is a bottleneck, use a step-managed container instead of `services:` and cache a saved image tar. GitHub Actions creates service containers before workflow steps run, so `actions/cache` cannot warm the image used by a `services:` block.

```yaml
jobs:
  sql-integration-tests:
    runs-on: ubuntu-latest
    env:
      SQL_IMAGE: mcr.microsoft.com/mssql/server:2022-latest
      SQL_IMAGE_CACHE: /tmp/mssql-server-2022-latest.tar
      SQL_PASSWORD: "Your_strong_password123"
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '8.0.x'
      - uses: actions/cache@v4
        id: sql-image-cache
        with:
          path: ${{ env.SQL_IMAGE_CACHE }}
          key: docker-image-mssql-server-2022-latest
      - name: Load cached SQL Server image
        if: steps.sql-image-cache.outputs.cache-hit == 'true'
        shell: pwsh
        run: docker load --input $env:SQL_IMAGE_CACHE
      - name: Pull and cache SQL Server image
        if: steps.sql-image-cache.outputs.cache-hit != 'true'
        shell: pwsh
        run: |
          docker pull $env:SQL_IMAGE
          docker save $env:SQL_IMAGE --output $env:SQL_IMAGE_CACHE
      - name: Start SQL Server
        shell: pwsh
        run: |
          docker run --detach --name sqlserver `
            --env ACCEPT_EULA=Y `
            --env "MSSQL_SA_PASSWORD=$env:SQL_PASSWORD" `
            --publish 1433:1433 `
            $env:SQL_IMAGE

          for ($attempt = 1; $attempt -le 30; $attempt++) {
            docker exec sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P $env:SQL_PASSWORD -C -Q "SELECT 1"
            if ($LASTEXITCODE -eq 0) { break }
            Start-Sleep -Seconds 5
          }

          if ($LASTEXITCODE -ne 0) { throw "SQL Server did not become ready" }
      - run: dotnet test --filter "Category=SqlIntegration"
        shell: pwsh
        env:
          ConnectionStrings__Default: "Server=localhost,1433;Database=IntegrationTests;User Id=sa;Password=${{ env.SQL_PASSWORD }};TrustServerCertificate=True;"
```

For cached images, prefer a fixed image tag or digest and include it in the cache key. If using a mutable tag such as `2022-latest`, change the cache key deliberately when the image should be refreshed.
