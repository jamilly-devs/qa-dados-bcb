import sys
sys.stdout.reconfigure(encoding='utf-8')
import csv
from datetime import datetime

INPUT_FILE = "selic_bruto.csv"
OUTPUT_FILE = "selic_limpo.csv"


def main():
    with open(INPUT_FILE, newline="", encoding="utf-8") as arquivo:
        linhas_originais = list(csv.DictReader(arquivo))

    total_antes = len(linhas_originais)
    linhas_limpas = []
    linhas_com_erro = []

    for linha in linhas_originais:
        try:
            data_convertida = datetime.strptime(linha["data"], "%d/%m/%Y").date()
            valor_convertido = float(linha["valor"])
        except (ValueError, TypeError):
            # data ou valor não converteram, guarda a linha à parte
            linhas_com_erro.append(linha)
            continue

        linhas_limpas.append({"data": data_convertida.isoformat(), "valor": valor_convertido})

    # garantia extra: nenhuma linha limpa deveria ficar com campo vazio
    assert all(l["data"] and l["valor"] is not None for l in linhas_limpas)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as arquivo_csv:
        writer = csv.DictWriter(arquivo_csv, fieldnames=["data", "valor"])
        writer.writeheader()
        writer.writerows(linhas_limpas)

    print("Transformação concluída.")
    print(f"Linhas antes da transformação: {total_antes}")
    print(f"Linhas depois da transformação: {len(linhas_limpas)}")
    print(f"Linhas com problema de conversão: {len(linhas_com_erro)}")
    if linhas_com_erro:
        print("Detalhe das linhas com problema (achado de qualidade de dado):")
        for linha in linhas_com_erro:
            print(f"  {linha}")
    print(f"Arquivo salvo como: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
