-- O nome amigável será enriquecido com o Cadastro e-MEC/Censo Superior.
SELECT
    co_curso,
    co_grupo,
    nome_area,
    modalidade,
    media_nt_ger,
    quantidade_notas_validas
FROM gold_desempenho_curso
WHERE co_ies = 555
  AND media_nt_ger IS NOT NULL
ORDER BY media_nt_ger DESC, quantidade_notas_validas DESC
LIMIT 10;
