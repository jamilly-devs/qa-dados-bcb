import sys
sys.stdout.reconfigure(encoding='utf-8')
import csv
import socket
import urllib3.util.connection as urllib3_connection
import requests

URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json"
OUTPUT_FILE = "ipca_bruto.csv"

# IPv6 dava timeout nessa API. forço IPv4 pra evitar isso.
urllib3_connection.allowed_gai_family = lambda: socket.AF_INET


def main():
    response = requests.get(URL, timeout=30)

    # se não vier status 200, para aqui e mostra o erro
    response.raise_for_status()

    dados = response.json()

    # a API pode responder 200 com lista vazia, então checo isso também
    if not dados:
        print("A API retornou uma lista vazia. Nenhum arquivo foi gerado.")
        return

    campos = list(dados[0].keys())

    # conta quantos registros têm algum campo em branco
    registros_com_campo_vazio = 0
    for registro in dados:
        if any(str(valor).strip() == "" for valor in registro.values()):
            registros_com_campo_vazio += 1

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as arquivo_csv:
        writer = csv.DictWriter(arquivo_csv, fieldnames=campos)
        writer.writeheader()
        writer.writerows(dados)

    print("Extração concluída com sucesso.")
    print(f"Status HTTP: {response.status_code}")
    print(f"Total de registros recebidos: {len(dados)}")
    print(f"Registros com algum campo vazio: {registros_com_campo_vazio}")
    print(f"Arquivo salvo como: {OUTPUT_FILE}")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.RequestException as erro:
        print(f"Falha na chamada à API do BCB: {erro}")
