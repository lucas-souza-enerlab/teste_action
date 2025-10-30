import requests, json, os, sys, pathlib

TB_URL  = os.getenv("TB_URL")      # ex.: https://iot.enerlab.io
TB_USER = os.getenv("TB_USER")     # virá dos Secrets
TB_PASS = os.getenv("TB_PASS")     # virá dos Secrets

def get_token():
    url = f"{TB_URL}/api/auth/login"
    r = requests.post(url, json={"username": TB_USER, "password": TB_PASS})
    r.raise_for_status()
    return r.json()["token"]

def get_gateway_id(token, gateway_name):
    url = f"{TB_URL}/api/tenant/devices?deviceName={gateway_name}"
    r = requests.get(url, headers={"X-Authorization": f"Bearer {token}"})
    if r.status_code != 200:
        raise SystemExit(f"[{gateway_name}] erro ao buscar gateway: {r.status_code} {r.text}")
    data = r.json()
    if "id" in data and "id" in data["id"]:
        return data["id"]["id"]
    raise SystemExit(f"[{gateway_name}] gateway não encontrado")

def update_connector(token, device_id, connector_name, connector_json):
    url = f"{TB_URL}/api/plugins/telemetry/DEVICE/{device_id}/SHARED_SCOPE"
    headers = {"Content-Type": "application/json", "X-Authorization": f"Bearer {token}"}
    body = {connector_name: connector_json}
    r = requests.post(url, headers=headers, data=json.dumps(body))
    if r.status_code == 200:
        print(f"✅ {connector_name} atualizado em {device_id}")
    else:
        print(f"❌ {connector_name} falhou: {r.status_code} {r.text}")

def infer_from_path(path):
    p = pathlib.Path(path)
    gateway_name = p.parent.name                       # .../GW-SCIESP-2/modbus-1.json
    connector_name = p.stem.upper()                    # modbus-1.json -> MODBUS-1
    with open(path, "r") as f:
        connector_json = json.load(f)                  # conteúdo do arquivo é só o bloco do conector
    return gateway_name, connector_name, connector_json

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python update_connector_repo.py <arquivo.json> [<arquivo2.json> ...]")
        sys.exit(1)

    # sanity checks
    for var in ("TB_URL","TB_USER","TB_PASS"):
        if not os.getenv(var):
            raise SystemExit(f"Faltando variável de ambiente: {var}")

    token = get_token()

    for path in sys.argv[1:]:
        gw, conn, payload = infer_from_path(path)
        print(f"🔎 Gateway={gw} | Conector={conn} | Arquivo={path}")
        device_id = get_gateway_id(token, gw)
        update_connector(token, device_id, conn, payload)
