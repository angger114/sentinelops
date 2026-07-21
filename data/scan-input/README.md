The Distributed Map ItemReader reads `inventory/<findingId>.json` from the **scan-input S3 bucket**
(not this folder). Generate it by invoking `sentinel-fn-init` with `events/init-payload.json`.
This folder just documents the expected shape:

```json
[ { "resourceArn": "...", "resourceId": "sg-0001", "public": false, "encrypted": true }, ... ]
```
