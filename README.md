# roproxy-gamepasses-py

REST service that lists gamepasses and prices from a Roblox user’s public universes via RoProxy.

## Endpoints
GET /healthz
GET /user/{userId}/gamepasses
GET /user/{userId}/gamepasses.html

## Local run
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python app.py  # http://localhost:8000

## Deploy on Render
Push this repo. Create a Web Service. Use the included render.yaml or set the start command to the Procfile command.
