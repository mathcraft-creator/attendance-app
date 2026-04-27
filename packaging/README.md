# Packaging Guide

## 1) Source package zip

```bash
bash scripts/package_project.sh
```

Output:
- `dist/attendance-app-package-<timestamp>.zip`

## 2) Offline wheelhouse (run in online environment)

```bash
bash scripts/build_wheelhouse.sh
```

Output:
- `wheelhouse/` with downloaded wheels/sdists

## 3) Offline installation

```bash
pip install --no-index --find-links=wheelhouse -r requirements.txt
```

## Notes
- If proxy/certificate is required, configure `HTTP_PROXY`, `HTTPS_PROXY`, and trusted certs before running download.
- `wheelhouse` should be generated in a network-enabled environment and then copied together with the source package zip.
