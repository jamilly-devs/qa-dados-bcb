"""
Mesma ideia do build_ipca_suite.py, mas pra série da Selic (série 11).
Monta a suite de expectations em cima do selic_limpo.csv, roda tudo e
gera o relatorio (Data Docs) no final.
"""
import datetime

import pandas as pd

import great_expectations as gx
import great_expectations.expectations as gxe
from great_expectations.checkpoint import UpdateDataDocsAction

context = gx.get_context(mode="file")

# a série do IPCA já tinha datasource/asset prontos de antes. pra Selic
# preciso criar isso primeiro (add_or_update evita erro se já existir)
datasource = context.data_sources.add_or_update_pandas_filesystem(
    name="selic_source", base_directory="."
)
try:
    asset = datasource.get_asset("selic_limpo")
except LookupError:
    asset = datasource.add_csv_asset(name="selic_limpo", parse_dates=["data"])

try:
    batch_definition = asset.get_batch_definition("selic_limpo_batch")
except KeyError:
    batch_definition = asset.add_batch_definition_path(
        name="selic_limpo_batch", path="selic_limpo.csv"
    )

# quantidade de dias úteis esperada entre a primeira e a última data,
# usada mais pra frente na checagem de dia faltando
df_atual = pd.read_csv("selic_limpo.csv", parse_dates=["data"])
dias_uteis = pd.bdate_range(start=df_atual["data"].min(), end=df_atual["data"].max())
qtd_dias_uteis = len(dias_uteis)

suite = gx.ExpectationSuite(name="selic_qualidade")

# regra 1: "valor" não pode ser nulo
suite.add_expectation(
    gxe.ExpectColumnValuesToNotBeNull(column="valor")
)

# regra 2: "valor" tem que ser número (float), não texto
suite.add_expectation(
    gxe.ExpectColumnValuesToBeOfType(column="valor", type_="float64")
)

# regra 3: "data" também não pode ser nula
suite.add_expectation(
    gxe.ExpectColumnValuesToNotBeNull(column="data")
)

# regra 4: não pode ter data repetida
suite.add_expectation(
    gxe.ExpectColumnValuesToBeUnique(column="data")
)

# regra 5: valor é a Selic diária em %, não anual -- por isso os números são pequenos, tipo 0.05
suite.add_expectation(
    gxe.ExpectColumnValuesToBeBetween(column="valor", min_value=0, max_value=0.2)
)

# regra 6: linhas deveriam ficar perto da contagem de dias úteis do
# período. dou uma margem de 10% porque feriado nacional tira dia útil
# e o pandas sozinho não sabe contar isso
suite.add_expectation(
    gxe.ExpectTableRowCountToBeBetween(
        min_value=int(qtd_dias_uteis * 0.9), max_value=qtd_dias_uteis
    )
)

# regra 7: não pode ter data no futuro
suite.add_expectation(
    gxe.ExpectColumnValuesToBeBetween(
        column="data", max_value=datetime.datetime.now()
    )
)

context.suites.add_or_update(suite)

validation_definition = gx.ValidationDefinition(
    name="selic_qualidade_validation",
    data=batch_definition,
    suite=suite,
)
validation_definition = context.validation_definitions.add_or_update(validation_definition)

checkpoint = gx.Checkpoint(
    name="selic_qualidade_checkpoint",
    validation_definitions=[validation_definition],
    actions=[UpdateDataDocsAction(name="update_data_docs")],
)
checkpoint = context.checkpoints.add_or_update(checkpoint)

result = checkpoint.run()

print("Sucesso geral da suite:", result.success)
print()
for validation_result in result.run_results.values():
    for r in validation_result.results:
        status = "PASSOU" if r.success else "FALHOU"
        print(f"[{status}] {r.expectation_config.type} -> {r.expectation_config.kwargs}")

print()
print("Data Docs:")
for site in context.get_docs_sites_urls():
    print(f"  {site['site_name']}: {site['site_url']}")
