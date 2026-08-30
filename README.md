# Desafio Técnico de Analista de Dados Pleno

Pipeline de processamento de Microdados do ENADE 2023 usando Python, DuckDB,
Parquet, Streamlit e Docker Compose.

## Execução

O pipeline ingere os 32 arquivos na camada Bronze, cria 32 arquivos
Parquet tipados e tratados na Silver e produz uma Gold agregada por curso.

## Como executar

Execute o arquivo .bat "Iniciar"

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

## Q1 — A Unifor está no ENADE 2023?

A Universidade de Fortaleza está presente no ENADE 2023, código e-MEC
**555**. Foram identificados **17 cursos**, em **17 áreas**, todos presenciais.

## Q2 — Presencial x EaD

| Modalidade | Média NT_GER |
|---|---:|
| EaD | 38,90 |
| Presencial | 49,73 |

A diferença observada é de **10,83 pontos** a favor da modalidade presencial.

## Q3 — Top 10 cursos/áreas da Unifor

| Pos. | CO_CURSO | Área | Média NT_GER | Notas válidas |
|---:|---:|---|---:|---:|
| 1 | 93001 | Medicina | 68,89 | 196 |
| 2 | 11719 | Enfermagem | 60,98 | 57 |
| 3 | 18324 | Arquitetura e Urbanismo | 58,92 | 144 |
| 4 | 11718 | Fisioterapia | 57,74 | 52 |
| 5 | 18325 | Farmácia | 54,19 | 42 |
| 6 | 11731 | Odontologia | 52,95 | 149 |
| 7 | 1315325 | Tecnologia em Estética e Cosmética | 51,94 | 23 |
| 8 | 56630 | Nutrição | 51,85 | 93 |
| 9 | 1357703 | Medicina Veterinária | 51,30 | 92 |
| 10 | 107686 | Engenharia Ambiental | 51,07 | 16 |


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
