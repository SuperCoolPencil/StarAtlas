# StarAtlas

StarAtlas generates stargazer community visuals (world map + top companies) directly inside your GitHub Actions runner.

## Usage

```yaml
name: StarAtlas

on:
  schedule:
    - cron: "0 * * * *"
  workflow_dispatch: {}

permissions:
  contents: write

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: supercoolpencil/staratlas@v1
        with:
          output-dir: staratlas
          html: "true"
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore(staratlas): update stargazer visuals"
          file_pattern: staratlas/*
```

## Embed

```md
![StarAtlas Map](./staratlas/staratlas-map.png)
![StarAtlas Top Companies](./staratlas/staratlas-companies.svg)
```
