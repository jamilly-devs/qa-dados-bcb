"""
Primeiro script que escrevi testando o Great Expectations: só pra ver se
eu conseguia conectar no ipca_limpo.csv e ler os dados através da lib.
"""
import great_expectations as gx

context = gx.get_context(mode="file")

datasource = context.data_sources.get("ipca_source")
asset = datasource.get_asset("ipca_limpo")
batch_definition = asset.add_batch_definition_path(
    name="ipca_limpo_batch", path="ipca_limpo.csv"
)

print("Datasource:", datasource.name)
print("Asset:", asset.name)
print("BatchDefinition:", batch_definition.name)

batch = batch_definition.get_batch()
df = batch.data.dataframe
print("Linhas lidas:", len(df))
print(df.head())
