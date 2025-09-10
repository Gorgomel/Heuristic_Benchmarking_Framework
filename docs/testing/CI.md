- name: Run pytest + coverage
  run: poetry run pytest

- name: Upload coverage.xml
  uses: actions/upload-artifact@v4
  with:
    name: coverage-xml
    path: coverage.xml

# (opcional) construir docs
- name: Build docs
  run: poetry run mkdocs build
- name: Upload site
  uses: actions/upload-artifact@v4
  with:
    name: site
    path: site
