# Changelog

## Unreleased

- Give concurrent uploads unique job IDs and reject invalid modes, unsupported files and directory-bearing filenames before writing data.
- Limit cleanup to files belonging to expired, completed or failed jobs.
- Preserve leading zeroes in CPF/CNPJ fields, retain newer duplicate records and handle missing optional contact columns.
- Keep numeric quality scores out of date detection and preserve the caller's labels during model training.
- Return a nonzero status when a pipeline command fails and launch the maintained backend from any working directory.
- Add a synthetic offline example, temporary test artifacts and CI coverage for the maintained application.
- Report API version `1.0.1` consistently in OpenAPI, health and fallback root responses. The repository has no tagged release series.

The changes above apply to the maintained CRM application. Historical experiments and the attributed weather ETL tutorial are unchanged.
