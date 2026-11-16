"""Inicia a API FastAPI.  Uso (raiz do projeto):  python Code/run_api.py [--porta 8000]"""

import argparse

import uvicorn

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--porta", type=int, default=8000)
    args = p.parse_args()
    # Code/ já está no sys.path (é a pasta deste script): o pacote `dengue` é encontrado.
    uvicorn.run("dengue.adapters.inbound.api_fastapi.app:app", host=args.host, port=args.porta)
