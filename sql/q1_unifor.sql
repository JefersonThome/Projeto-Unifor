SELECT
    co_ies,
    COUNT(DISTINCT co_curso) AS quantidade_cursos,
    co_grupo,
    nome_area,
    modalidade
FROM gold_desempenho_curso
WHERE co_ies = 555
GROUP BY co_ies, co_grupo, nome_area, modalidade
ORDER BY co_grupo, modalidade;
