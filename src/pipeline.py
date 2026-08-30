from __future__ import annotations

import csv
import re
import shutil
import zipfile
from pathlib import Path

import duckdb
import requests


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "source_data"
DATA_DIR = ROOT / "data"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"
DB_PATH = DATA_DIR / "enade.duckdb"
ZIP_PATH = SOURCE_DIR / "microdados_enade_2023.zip"
DOWNLOAD_URL = "https://download.inep.gov.br/microdados/microdados_enade_2023.zip"
AREA_NAMES = {
    5: "Medicina Veterinária", 6: "Odontologia", 12: "Medicina",
    17: "Agronomia", 19: "Farmácia", 21: "Arquitetura e Urbanismo",
    23: "Enfermagem", 27: "Fonoaudiologia", 28: "Nutrição",
    36: "Fisioterapia", 51: "Zootecnia", 55: "Biomedicina",
    69: "Tecnologia em Radiologia", 90: "Tecnologia em Agronegócios",
    91: "Tecnologia em Gestão Hospitalar", 92: "Tecnologia em Gestão Ambiental",
    95: "Tecnologia em Estética e Cosmética", 5710: "Engenharia Civil",
    5806: "Engenharia Elétrica", 5814: "Engenharia de Controle e Automação",
    5902: "Engenharia Mecânica", 6002: "Engenharia de Alimentos",
    6008: "Engenharia Química", 6208: "Engenharia de Produção",
    6307: "Engenharia Ambiental", 6405: "Engenharia Florestal",
    6410: "Tecnologia em Segurança no Trabalho",
    6411: "Engenharia de Computação I",
}


def ensure_directories() -> None:
    for path in (SOURCE_DIR, BRONZE_DIR, SILVER_DIR, GOLD_DIR):
        path.mkdir(parents=True, exist_ok=True)


def download_if_needed() -> None:
    if ZIP_PATH.exists() and ZIP_PATH.stat().st_size > 0:
        return
    print(f"Baixando {DOWNLOAD_URL}")
    try:
        with requests.get(DOWNLOAD_URL, stream=True, timeout=120) as response:
            response.raise_for_status()
            with ZIP_PATH.open("wb") as output:
                for chunk in response.iter_content(1024 * 1024):
                    output.write(chunk)
    except requests.RequestException as exc:
        raise RuntimeError(
            "O download do INEP falhou. Baixe microdados_enade_2023.zip "
            "manualmente e coloque-o em source_data/."
        ) from exc


def find_member(zf: zipfile.ZipFile, pattern: str) -> str:
    matches = [name for name in zf.namelist() if re.search(pattern, name, re.I)]
    if not matches:
        raise FileNotFoundError(f"Arquivo não encontrado no ZIP: {pattern}")
    return matches[0]


def extract_bronze() -> list[Path]:
    with zipfile.ZipFile(ZIP_PATH) as zf:
        members = [
            n for n in zf.namelist()
            if re.search(r"microdados2023_arq\d+\.txt$", n, re.I)
        ]
        if len(members) != 32:
            raise ValueError(f"Esperados 32 TXT; encontrados {len(members)}")
        outputs = []
        for member in members:
            target = BRONZE_DIR / Path(member).name.lower()
            with zf.open(member) as source, target.open("wb") as destination:
                shutil.copyfileobj(source, destination)
            outputs.append(target)
    return sorted(outputs, key=lambda p: int(re.search(r"arq(\d+)", p.name)[1]))


def detect_encoding(path: Path) -> str:
    for encoding in ("utf-8", "latin-1"):
        try:
            path.read_text(encoding=encoding)[:4096]
            return encoding
        except UnicodeDecodeError:
            continue
    return "latin-1"


def columns_of(path: Path, encoding: str) -> list[str]:
    with path.open(encoding=encoding, newline="") as stream:
        return next(csv.reader(stream, delimiter=";"))


def quoted(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def typed_expression(column: str) -> str:
    q = quoted(column)
    normalized = f"NULLIF(TRIM({q}), '')"
    if column.startswith("NT_"):
        return f"TRY_CAST(REPLACE({normalized}, ',', '.') AS DOUBLE) AS {q}"
    integer_prefixes = ("CO_", "TP_", "NU_", "ANO_")
    if column.startswith(integer_prefixes):
        return f"TRY_CAST({normalized} AS BIGINT) AS {q}"
    return f"{normalized} AS {q}"


def build_silver(con: duckdb.DuckDBPyConnection, txt_files: list[Path]) -> None:
    for path in txt_files:
        encoding = detect_encoding(path)
        columns = columns_of(path, encoding)
        select_list = ",\n".join(typed_expression(c) for c in columns)
        target = SILVER_DIR / path.with_suffix(".parquet").name
        source_sql = str(path).replace("'", "''")
        target_sql = str(target).replace("'", "''")
        con.execute(
            f"""
            COPY (
                SELECT {select_list}
                FROM read_csv(
                    '{source_sql}', delim=';', header=true,
                    all_varchar=true, encoding='{encoding}',
                    ignore_errors=false, strict_mode=true
                )
            ) TO '{target_sql}' (FORMAT PARQUET, COMPRESSION ZSTD)
            """
        )
        print(f"Silver criada: {target.name}")


def build_gold(con: duckdb.DuckDBPyConnection) -> None:
    arq1 = str(SILVER_DIR / "microdados2023_arq1.parquet").replace("'", "''")
    arq3 = str(SILVER_DIR / "microdados2023_arq3.parquet").replace("'", "''")
    gold = str(GOLD_DIR / "desempenho_curso.parquet").replace("'", "''")
    area_case = "CASE CO_GRUPO " + " ".join(
        f"WHEN {code} THEN '{name}'" for code, name in AREA_NAMES.items()
    ) + " ELSE 'Área não mapeada' END"
    con.execute(
        f"""
        CREATE OR REPLACE TABLE dim_curso AS
        SELECT DISTINCT
            NU_ANO AS nu_ano,
            CO_CURSO AS co_curso,
            CO_IES AS co_ies,
            CO_CATEGAD AS co_categoria_administrativa,
            CO_ORGACAD AS co_organizacao_academica,
            CO_GRUPO AS co_grupo,
            {area_case} AS nome_area,
            CO_MODALIDADE AS co_modalidade,
            CASE CO_MODALIDADE WHEN 0 THEN 'EaD' WHEN 1 THEN 'Presencial' END
                AS modalidade,
            CO_MUNIC_CURSO AS co_municipio_curso,
            CO_UF_CURSO AS co_uf_curso,
            CO_REGIAO_CURSO AS co_regiao_curso
        FROM read_parquet('{arq1}');

        CREATE OR REPLACE TABLE fato_desempenho_curso AS
        SELECT
            NU_ANO AS nu_ano,
            CO_CURSO AS co_curso,
            COUNT(*) AS quantidade_registros,
            COUNT(NT_GER) AS quantidade_notas_validas,
            COUNT(*) - COUNT(NT_GER) AS quantidade_notas_nulas,
            (COUNT(*) - COUNT(NT_GER))::DOUBLE / NULLIF(COUNT(*), 0)
                AS percentual_notas_nulas,
            AVG(NT_GER) AS media_nt_ger,
            MEDIAN(NT_GER) AS mediana_nt_ger,
            STDDEV_SAMP(NT_GER) AS desvio_padrao_nt_ger
        FROM read_parquet('{arq3}')
        GROUP BY NU_ANO, CO_CURSO;

        CREATE OR REPLACE TABLE gold_desempenho_curso AS
        SELECT d.*, f.* EXCLUDE (nu_ano, co_curso)
        FROM dim_curso d
        LEFT JOIN fato_desempenho_curso f USING (nu_ano, co_curso);

        COPY gold_desempenho_curso TO '{gold}'
        (FORMAT PARQUET, COMPRESSION ZSTD);

        CREATE OR REPLACE TABLE gold_modalidade AS
        SELECT
            d.modalidade,
            COUNT(n.NT_GER) AS quantidade_notas_validas,
            AVG(n.NT_GER) AS media_nt_ger,
            MEDIAN(n.NT_GER) AS mediana_nt_ger,
            STDDEV_SAMP(n.NT_GER) AS desvio_padrao_nt_ger
        FROM read_parquet('{arq3}') n
        JOIN dim_curso d
          ON n.NU_ANO = d.nu_ano AND n.CO_CURSO = d.co_curso
        WHERE n.NT_GER IS NOT NULL
        GROUP BY d.modalidade;
        """
    )


def run_quality_checks(con: duckdb.DuckDBPyConnection) -> None:
    checks = {
        "32 arquivos Silver": len(list(SILVER_DIR.glob("microdados2023_arq*.parquet"))) == 32,
        "CO_CURSO único na dimensão": con.execute(
            "SELECT COUNT(*) = COUNT(DISTINCT (nu_ano, co_curso)) FROM dim_curso"
        ).fetchone()[0],
        "Notas entre 0 e 100": con.execute(
            "SELECT COUNT(*) = 0 FROM fato_desempenho_curso "
            "WHERE media_nt_ger NOT BETWEEN 0 AND 100"
        ).fetchone()[0],
        "Modalidades válidas": con.execute(
            "SELECT COUNT(*) = 0 FROM dim_curso WHERE co_modalidade NOT IN (0, 1)"
        ).fetchone()[0],
    }
    failures = [name for name, passed in checks.items() if not passed]
    for name, passed in checks.items():
        print(f"[{'OK' if passed else 'FALHA'}] {name}")
    if failures:
        raise AssertionError("Falhas de qualidade: " + ", ".join(failures))


def main() -> None:
    ensure_directories()
    download_if_needed()
    txt_files = extract_bronze()
    with duckdb.connect(str(DB_PATH)) as con:
        build_silver(con, txt_files)
        build_gold(con)
        run_quality_checks(con)
    print("Pipeline concluído.")


if __name__ == "__main__":
    main()
