# ENADE 2023 — Desafio de Analista de Dados Pleno

Pipeline analítico dos Microdados do ENADE 2023 usando Python, DuckDB,
Parquet, Streamlit e Docker Compose.

## Estado atual

O pipeline ingere os 32 arquivos, preserva os TXT na Bronze, cria 32 arquivos
Parquet tipados na Silver e produz uma Gold agregada por curso.

## Como executar

```bash
docker compose up --build
```

Depois, acesse `http://localhost:8501`.

Se o servidor do INEP estiver indisponível, baixe manualmente o arquivo
`microdados_enade_2023.zip` e coloque-o na pasta `source_data/`.

## Arquitetura

- **Bronze:** os 32 arquivos TXT exatamente como publicados pelo INEP.
- **Silver:** um Parquet tipado para cada TXT; vazios são convertidos em nulos.
- **Gold:** dimensão de curso e fato de desempenho agregada por `CO_CURSO`.

## Restrição de privacidade e granularidade

Os arquivos são ordenados por variáveis diferentes para reduzir o risco de
reidentificação. Portanto, a linha N de um arquivo não representa o mesmo
estudante da linha N de outro arquivo. Não há joins no nível do estudante.
Qualquer combinação entre arquivos diferentes ocorre somente após agregação
por `CO_CURSO`, conforme o manual do INEP.

## Definição da nota

`NT_GER` é convertida para número decimal; campos vazios tornam-se `NULL`, não
zero. A Gold guarda quantidade de registros, notas válidas, notas nulas, média,
mediana e desvio-padrão por curso.

## Respostas às perguntas de negócio

### Q1 — A Unifor está no ENADE 2023?

Sim. Seu código no Cadastro e-MEC é **555**. A base contém **17 cursos/áreas**
da Unifor, todos presenciais, e 1.235 notas válidas. As áreas estão disponíveis
na consulta `sql/q1_unifor.sql` e no dashboard.

### Q2 — Presencial x EaD

A média nacional ponderada pelos estudantes é **49,73 no Presencial** e
**38,90 no EaD**, diferença de 10,83 pontos. A consulta usa somente `NT_GER`
válida e apresenta também mediana, desvio-padrão e tamanho das amostras.

### Q3 — Top 10 da Unifor

Medicina lidera com média **68,89**, seguida por Enfermagem (**60,98**) e
Arquitetura e Urbanismo (**58,92**). O resultado sustenta parcialmente a
expectativa de melhor desempenho dos cursos tradicionais de saúde: oito das
dez primeiras áreas estão ligadas à saúde, embora Arquitetura apareça em terceiro.

As consultas estão em `sql/`. A comparação Presencial x EaD apresenta a média
ponderada pela quantidade de estudantes e também a média simples entre cursos,
evitando esconder o efeito do tamanho de cada curso.

## Limitações conhecidas

- O nome exibido é a área de enquadramento oficial (`CO_GRUPO`). Para distinguir
  habilitações com nomes próprios, seria necessário enriquecer `CO_CURSO` com o
  Cadastro e-MEC ou o Censo da Educação Superior.
- Os pontos extras de renda e percepção devem ser agregados separadamente por
  curso antes de qualquer cruzamento com desempenho.

## Fontes

- Microdados do ENADE: https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados
- Cadastro e-MEC: https://emec.mec.gov.br/
- Registro da Unifor no e-MEC: https://emec.mec.gov.br/emec/consulta-cadastro/detalhes-ies/d96957f455f6405d14c6542552b0f6eb/NTU1
