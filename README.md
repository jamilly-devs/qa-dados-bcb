# qa-dados-bcb

Esse é um projeto pequeno que fiz pra estudar QA de dados na prática. A ideia
foi pegar uma série de dados pública (o IPCA, divulgado pelo Banco Central do
Brasil) e montar um pipeline simples de extração, tratamento e validação, pra
treinar Python e conhecer o Great Expectations, que era uma ferramenta que eu
nunca tinha usado antes.

Depois de fechar isso pro IPCA, repeti o mesmo processo pra outra série do
BCB, a Selic (série 11), pra ver se o que eu tinha montado fazia sentido de
verdade ou se só "funcionava por sorte" com uma série só.

Não é um projeto perfeito nem "pronto para produção", é material de estudo
mesmo, e ainda estou aprendendo boa parte do que tem aqui.

## O que o projeto faz

São três passos, cada um em um script:

1. **`extract.py`** — busca os dados do IPCA direto na API do Banco Central
   e salva tudo cru em `ipca_bruto.csv`.
2. **`transform.py`** — pega esse CSV cru, converte data e valor pros tipos
   certos, separa linhas que não converteram (se tiver alguma) e gera o
   `ipca_limpo.csv`.
3. **`build_ipca_suite.py`** — usa o Great Expectations pra rodar um conjunto
   de regras de qualidade (as "expectations") em cima do `ipca_limpo.csv` e
   gera um relatório (Data Docs) mostrando o que passou e o que falhou.

Tem também um `setup_gx_datasource.py`, que foi o primeiro script que escrevi
só pra entender como o Great Expectations lê um CSV, deixei ele aqui como
registro dos primeiros passos.

### Depois, repeti o processo com a Selic (série 11)

A série 11 do BCB é a taxa Selic, só que **diária** e em **percentual ao
dia**, não ao ano, isso me confundiu no começo, porque a Selic que a gente
vê no noticiário é sempre a taxa anual (tipo "13,75% ao ano"). Os valores
dessa série são bem pequenos (tipo 0.05), porque é o percentual de um dia só.

São mais três scripts, no mesmo esquema dos anteriores:

1. **`extract_selic.py`** — busca a série 11 na API do BCB e salva em
   `selic_bruto.csv`. Como é série diária, a API do BCB só deixa consultar
   com uma data inicial (janela de no máximo 10 anos), então o script pede
   os últimos 10 anos a partir de hoje.
2. **`transform_selic.py`** — mesma lógica do `transform.py`, convertendo
   data e valor e gerando o `selic_limpo.csv`.
3. **`build_selic_suite.py`** — monta e roda a suite `selic_qualidade` no
   Great Expectations, igual fiz pro IPCA.

## Como rodar

```bash
python extract.py
python transform.py
python build_ipca_suite.py

python extract_selic.py
python transform_selic.py
python build_selic_suite.py
```

No final de cada script `build_*_suite.py` ele imprime no terminal quais
regras passaram e quais falharam, e mostra o link do Data Docs (um HTML
gerado pelo próprio Great Expectations) pra visualizar o resultado.

Também dá pra rodar as duas suites de uma vez com o pytest, o mesmo tipo de
comando único que já uso no dia a dia com Cypress/Jest:

```bash
pytest tests/
```

## As regras de qualidade que criei

No `build_ipca_suite.py` tem 7 expectations, tipo: valor e data não podem
ser nulos, data não pode se repetir, não pode faltar mês na série, não pode
ter data no futuro, etc. Comentei cada uma no código explicando por que
achei que fazia sentido checar aquilo.

## Uma coisa que descobri estudando isso (e decidi não "corrigir")

A regra 5 espera que o valor mensal do IPCA fique entre -5 e 15. Quando rodei
a suite pela primeira vez, ela falhava pra vários meses antigos, lá do fim
dos anos 80 e começo dos 90. No começo achei que tinha errado a regra, mas
pesquisando descobri que aquele período foi de hiperinflação no Brasil, com o
IPCA mensal passando de 80% em alguns meses, bem antes do Plano Real (1994),
que foi quando a inflação começou a ficar mais estável.

Ou seja: a regra "falhar" ali não é um bug, é ela fazendo o que deveria
avisando que aqueles valores fogem muito do padrão que eu defini pensando no
Brasil pós-Plano Real. Decidi deixar assim de propósito, em vez de ampliar o
range só pra "passar tudo", porque achei um achado interessante pra registrar.

## As regras de qualidade da Selic

O `build_selic_suite.py` também tem 7 expectations, no mesmo espírito das do
IPCA (valor e data não nulos, data não duplicada, data não no futuro, etc.).
Duas coisas mudaram em relação ao IPCA:

- **O range de valor** ficou entre 0 e 0.2, já que aqui o valor é a Selic
  diária em percentual (não anual), expliquei isso melhor lá em cima.
- **A regra de "não pode faltar linha"** não deu pra copiar igual do IPCA.
  No IPCA eu comparava a quantidade de linhas com a quantidade de meses
  esperados, porque é uma série mensal. A Selic é por dia útil, e a
  quantidade de dias úteis muda todo ano por causa dos feriados nacionais
  o pandas sozinho não sabe quais dias são feriado, só sabe tirar fim de
  semana. Então, em vez de exigir um número exato de linhas, deixei uma
  margem de 10% pra cima/baixo da contagem de dias úteis do período.

Diferente do IPCA, aqui as 7 regras passaram todas, não achei nenhum
comportamento inesperado na Selic dos últimos 10 anos (que foi o período que
consegui puxar, por causa do limite da API pra séries diárias).

## Rodando tudo com pytest

Criei uma pasta `tests/` com `test_qualidade_dados.py`, com uma função de
teste pra cada suite (`test_ipca_qualidade` e `test_selic_qualidade`). Cada
uma roda o checkpoint do Great Expectations correspondente e faz o teste
falhar se alguma regra não passar igual eu já fazia no Cypress/Jest, só
que aqui quem roda por baixo é o Great Expectations, não uma asserção minha.

Uma exceção: no `test_ipca_qualidade`, a regra do range de valor (a que
falha de propósito nos meses de hiperinflação) é ignorada só na hora de
decidir se o teste do pytest quebra ou não. A suite continua rodando essa
regra normalmente e o Data Docs continua mostrando a falha real só não
quero que o pytest fique vermelho por causa de um achado que já sei que é
esperado.

## O que ainda quero estudar/melhorar

- Entender melhor outros tipos de expectation que o Great Expectations
  oferece (ainda usei só uma parte pequena do que existe).
- Ver como automatizar a execução dos três scripts em sequência.
- Aprender a interpretar melhor o Data Docs gerado.

Ainda to aprendendo bastante, então se tiver alguma parte meio torta ou que 
dava pra fazer diferente, é porque realmente ainda tô entendendo esses conceitos.
