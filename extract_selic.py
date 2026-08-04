import sys
sys.stdout.reconfigure(encoding='utf-8')
import csv
import socket
from datetime import date
import urllib3.util.connection as urllib3_connection
import requests

URL_BASE = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json"
OUTPUT_FILE = "selic_bruto.csv"

# IPv6 dava timeout nessa API. forço IPv4 pra evitar isso.
urllib3_connection.allowed_gai_family = lambda: socket.AF_INET


def data_inicial_10_anos_atras():
    hoje = date.today()
    try:
        return hoje.replace(year=hoje.year - 10)
    except ValueError:
        # cai num 29/fev sem ano bissexto 10 anos atrás
        return hoje.replace(year=hoje.year - 10, day=28)


def main():
    # série 11 é diária, e a API do BCB só aceita consulta com data inicial
    # pra série diária (janela de no máximo 10 anos), diferente da série
    # mensal do IPCA que buscamos sem filtro nenhum
    data_inicial = data_inicial_10_anos_atras().strftime("%d/%m/%Y")
    url = f"{URL_BASE}&dataInicial={data_inicial}"

    response = requests.get(url, timeout=30)

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
