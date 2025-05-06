Pre-commit ist ein Framework, das Git-Hooks verwaltet und automatisiert. Sobald ihr es installiert und mit pre-commit install aktiviert habt, laufen bei jedem git commit vordefinierte Prüf- und Formatierungsskripte (Hooks). Diese überprüfen euren Code auf Stil, Syntax oder potentielle Fehler und formatieren ihn automatisch, ehe der Commit fertiggestellt wird. So stellt ihr sicher, dass alle Teammitglieder beim Einchecken stets den gleichen Qualitäts- und Style-Standard einhalten – ganz ohne manuelles Nacharbeiten.

## 1. Pre-commit installieren

1. Aktiviert euer virtuelles Environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

1. Installiert das Pre-commit-Paket:

   ```bash
   pip install --upgrade pip
   pip install pre-commit
   ```

______________________________________________________________________

## 2. Git-Hook installieren

Führt im Projekt-Root aus:

```bash
pre-commit install
```

Damit werden die Hooks aus eurer bereits vorhandenen `.pre-commit-config.yaml` bei jedem `git commit` ausgeführt.

______________________________________________________________________

## 3. Hooks einmalig auf alle Dateien anwenden

Um eure bestehende Codebasis sofort zu formatieren und zu prüfen, gebt ein:

```bash
pre-commit run --all-files
```

Alle Änderungen (Formatierungen, Sortierungen, Lint-Fixes) werden als unstaged Modifikationen angezeigt — einfach prüfen und committen.

______________________________________________________________________

## 4. Tipps & Troubleshooting

- **Pre-commit updaten**
  ```bash
  pre-commit autoupdate
  ```
- **Hook-Cache löschen** (wenn neue Hooks nicht geladen werden):
  ```bash
  pre-commit clean
  pre-commit install
  ```
- **Einen einzelnen Hook testen**:
  ```bash
  pre-commit run black --all-files
  ```
- **Fehlermeldungen** zu Längen- oder Import-Regeln lassen sich per `# noqa` oder `per-file-ignores` in eurer Flake8-Config unterdrücken.
