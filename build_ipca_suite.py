"""
Monta a suite de expectations (regras de qualidade) em cima do
ipca_limpo.csv, roda tudo e gera o relatorio (Data Docs) no final.
"""
import datetime

import pandas as pd

import great_expectations as gx
import great_expectations.expectations as gxe
from great_expectations.checkpoint import UpdateDataDocsAction

context = gx.get_context(mode="file")

datasource = context.data_sources.get("ipca_source")
asset = datasource.get_asset("ipca_limpo")
batch_definition = asset.get_batch_definition("ipca_limpo_batch")

# quantidade de meses esperada entre a primeira e a última data,
# usada mais pra frente na checagem de mês faltando
df_atual = pd.read_csv("ipca_limpo.csv", parse_dates=["data"])
meses_esperados = pd.date_range(
    start=df_atual["data"].min(), end=df_atual["data"].max(), freq="MS"
)
qtd_meses_esperada = len(meses_esperados)

suite = gx.ExpectationSuite(name="ipca_qualidade")

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

# regra 5: valor mensal do IPCA esperado entre -5 e 15.
# esse range não cobre os meses de hiperinflação antiga (~1988-1994),
# e tá certo, foi de propósito -- o range é pro Brasil pós-Plano Real.
suite.add_expectation(
    gxe.ExpectColumnValuesToBeBetween(column="valor", min_value=-5, max_value=15)
)

# regra 6: não pode faltar mês no meio da série (linhas x meses esperados)
suite.add_expectation(
    gxe.ExpectTableRowCountToEqual(value=qtd_meses_esperada)
)

# regra 7: não pode ter data no futuro
suite.add_expectation(
    gxe.ExpectColumnValuesToBeBetween(
        column="data", max_value=datetime.datetime.now()
    )
)

context.suites.add_or_update(suite)

validation_definition = gx.ValidationDefinition(
    name="ipca_qualidade_validation",
    data=batch_definition,
    suite=suite,
)
validation_definition = context.validation_definitions.add_or_update(validation_definition)

checkpoint = gx.Checkpoint(
    name="ipca_qualidade_checkpoint",
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
