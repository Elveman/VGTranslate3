import json, base64, pathlib, subprocess, time, requests

PNG = base64.b64encode(pathlib.Path("tests/hello.png").read_bytes()).decode()

def test_serve_hello(tmp_path):
    proc = subprocess.Popen(["python", "serve.py"], cwd=pathlib.Path(__file__).parents[1])
    time.sleep(2)
    try:
        r = requests.post("http://localhost:4404/service?target_lang=en",
                          data=json.dumps({"image": PNG}))
        assert r.status_code == 200
        payload = r.json()
        assert any(k in payload for k in ("blocks", "image"))
    finally:
        proc.terminate()
