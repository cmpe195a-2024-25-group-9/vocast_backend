# vocast_backend
vocast python backend to collect mic audio and stream to esp via udp

## use
to test, run the below command to start streaming to an esp on a specific IP address:
```bash
curl -X POST "http://127.0.0.1:8000/stream" -H "Content-Type: application/json" -d '{"start": true, "IP": "X.X.X.X"}'
```
to stop streaming
```bash
curl -X POST "http://127.0.0.1:8000/stream" -H "Content-Type: application/json" -d '{"start": false}'
```