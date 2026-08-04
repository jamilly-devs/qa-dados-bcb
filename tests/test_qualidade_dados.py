"""
Roda os checkpoints do Great Expectations (ipca_qualidade e
selic_qualidade) dentro do pytest, pra tudo rodar com um comando só.
Os checkpoints já foram criados pelos scripts build_ipca_suite.py e
build_selic_suite.py -- aqui só pego eles e rodo de novo.
"""
import great_expectations as gx

# essa é a regra do IPCA que falha de propósito nos meses de hiperinflação
# antiga (~1988-1994) -- não é bug, é achado documentado, então não travo
# o teste por causa dela
EXPECTATION_TYPE_HIPERINFLACAO = "expect_column_values_to_be_between"
EXPECTATION_COLUNA_HIPERINFLACAO = "valor"


def _rodar_checkpoint(nome):
    context = gx.get_context(mode="file")
    checkpoint = context.checkpoints.get(nome)
    run_result = checkpoint.run()

    resultados = []
    for validation_result in run_result.run_results.values():
        resultados.extend(validation_result.results)
    return resultados


def test_ipca_qualidade():
    for r in _rodar_checkpoint("ipca_qualidade_checkpoint"):
        kwargs = r.expectation_config.kwargs
        eh_regra_da_hiperinflacao = (
            r.expectation_config.type == EXPECTATION_TYPE_HIPERINFLACAO
            and kwargs.get("column") == EXPECTATION_COLUNA_HIPERINFLACAO
        )
        if eh_regra_da_hiperinflacao:
            continue
        assert r.success, f"{r.expectation_config.type} falhou: {kwargs}"


def test_selic_qualidade():
    for r in _rodar_checkpoint("selic_qualidade_checkpoint"):
        assert r.success, f"{r.expectation_config.type} falhou: {r.expectation_config.kwargs}"
