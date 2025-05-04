# vocast_backend
vocast python backend to collect mic audio and stream to esp via udp

## setting up
1. create `venv` with `python3 -m venv venv`
2. activate `venv` with `source venv/bin/activate`
3. install needed packages with `pip install -r requirements.txt`
4. (when done) deactivate `venv` with `deactivate`

## running
- use `fastapi dev main.py` to run normally
- use `uvicorn main:app --host 0.0.0.0 --port 8000 --reload` to run backend as admin

## use
to test, run the below command to start streaming to an esp on a specific IP address:
```bash
curl -X POST "http://127.0.0.1:8000/stream" -H "Content-Type: application/json" -d '{"start": true, "ip": "X.X.X.X"}'
```
to stop streaming
```bash
curl -X POST "http://127.0.0.1:8000/stream" -H "Content-Type: application/json" -d '{"start": false}'
```