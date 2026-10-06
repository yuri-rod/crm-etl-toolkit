@echo off
chcp 65001 > nul
echo ================================================================================
echo               PROCESSADOR DE DADOS UNIFICADO
echo ================================================================================
echo.
echo 🚀 Iniciando processamento dos arquivos Base JE*.csv...
echo.
python processador_dados_unificado.py
echo.
echo ================================================================================
echo ✅ PROCESSAMENTO CONCLUÍDO!
echo ================================================================================
echo.
echo 💡 Para analisar os dados processados, execute:
echo    python exemplo_uso_dados_finais.py
echo.
pause

