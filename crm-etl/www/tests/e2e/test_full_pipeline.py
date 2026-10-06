"""
Testes completos da pipeline ETL end-to-end
Sistema ETL Inteligente - CRM Tools

Testes que executam o fluxo completo:
1. Upload de arquivo
2. Configuração de pipeline  
3. Execução completa
4. Verificação de resultados
5. Download de resultados
"""

import pytest
import os
from pages import ETLPage


@pytest.mark.regression
@pytest.mark.slow
class TestFullPipeline:
    """Testes completos da pipeline ETL"""
    
    def test_complete_training_workflow_csv(self, etl_page: ETLPage, sample_csv_file: str):
        """
        Teste: Workflow completo de treinamento com arquivo CSV
        
        Fluxo:
        1. Upload de arquivo CSV
        2. Configuração para modo treinamento
        3. Execução da pipeline
        4. Verificação de resultados
        5. Download dos resultados
        """
        etl_page.log_step("=== TESTE: Workflow completo de treinamento CSV ===")
        
        # Passo 1: Carregar página e fazer upload
        etl_page.load_page()
        etl_page.verify_page_loaded()
        etl_page.upload_file(sample_csv_file)
        
        # Passo 2: Configurar pipeline para treinamento
        etl_page.configure_pipeline(
            mode="train",
            target_column="qualidade_lead",
            model_dir="./production_models/",
            enable_enrichment=False
        )
        
        # Passo 3: Executar pipeline
        etl_page.execute_pipeline()
        
        # Passo 4: Aguardar conclusão (até 2 minutos)
        etl_page.wait_for_pipeline_completion(timeout=120000)
        
        # Passo 5: Verificar resultados
        results = etl_page.verify_results_displayed()
        
        # Validações específicas
        assert int(results['total_records']) > 0, "Deve haver registros processados"
        assert int(results['features_created']) >= 0, "Features devem ter sido criadas"
        
        # Verificar acurácia (deve ser um percentual)
        accuracy_text = results['model_accuracy']
        if '%' in accuracy_text:
            accuracy_value = float(accuracy_text.replace('%', ''))
            assert 50 <= accuracy_value <= 100, f"Acurácia deve estar entre 50-100%: {accuracy_value}"
        
        # Passo 6: Exportar resultados
        downloaded_filename = etl_page.export_results()
        assert downloaded_filename is not None, "Arquivo deve ter sido baixado"
        assert "crm_result_" in downloaded_filename, "Nome do arquivo deve conter prefixo correto"
        
        etl_page.log_assertion("Workflow de treinamento CSV concluído com sucesso")
        
    @pytest.mark.skipif(
        "CI" in os.environ, 
        reason="Teste de Excel requer pandas - pode não estar disponível no CI"
    )
    def test_complete_training_workflow_excel(self, etl_page: ETLPage, sample_excel_file: str):
        """
        Teste: Workflow completo de treinamento com arquivo Excel
        
        Similar ao teste CSV, mas usando arquivo Excel
        """
        etl_page.log_step("=== TESTE: Workflow completo de treinamento Excel ===")
        
        # Passo 1: Carregar página e fazer upload
        etl_page.load_page()
        etl_page.verify_page_loaded()
        etl_page.upload_file(sample_excel_file)
        
        # Passo 2: Configurar pipeline
        etl_page.configure_pipeline(
            mode="train",
            target_column="qualidade_lead",
            enable_enrichment=True  # Testar com enriquecimento
        )
        
        # Passo 3: Executar e aguardar
        etl_page.execute_pipeline()
        etl_page.wait_for_pipeline_completion(timeout=150000)  # Mais tempo para Excel + enriquecimento
        
        # Passo 4: Verificar e exportar
        results = etl_page.verify_results_displayed()
        downloaded_filename = etl_page.export_results()
        
        # Validações
        assert int(results['total_records']) > 0
        assert downloaded_filename is not None
        
        etl_page.log_assertion("Workflow de treinamento Excel concluído com sucesso")
        
    def test_complete_prediction_workflow(self, etl_page: ETLPage, sample_csv_file: str):
        """
        Teste: Workflow completo de predição em lote
        
        Fluxo:
        1. Upload de arquivo
        2. Configuração para modo predição
        3. Execução da pipeline
        4. Verificação de resultados de predição
        5. Download dos resultados
        """
        etl_page.log_step("=== TESTE: Workflow completo de predição ===")
        
        # Passo 1: Setup
        etl_page.load_page()
        etl_page.upload_file(sample_csv_file)
        
        # Passo 2: Configurar para predição
        etl_page.configure_pipeline(
            mode="batch-predict",
            model_dir="./production_models/",
            output_filename="predictions_test_output.csv",
            enable_enrichment=False
        )
        
        # Passo 3: Executar
        etl_page.execute_pipeline()
        etl_page.wait_for_pipeline_completion(timeout=120000)
        
        # Passo 4: Verificar resultados
        results = etl_page.verify_results_displayed()
        
        # Para predição, a métrica de "acurácia" será o número de predições
        predictions_text = results['model_accuracy']
        # Pode ser um número (predições) ou percentual
        if predictions_text.isdigit():
            predictions_count = int(predictions_text)
            assert predictions_count > 0, "Deve haver predições geradas"
        
        # Passo 5: Download
        downloaded_filename = etl_page.export_results()
        assert "predictions_test_output" in downloaded_filename or "crm_result_" in downloaded_filename
        
        etl_page.log_assertion("Workflow de predição concluído com sucesso")


@pytest.mark.regression
class TestPipelineConfiguration:
    """Testes de diferentes configurações da pipeline"""
    
    def test_different_target_columns(self, etl_page: ETLPage, sample_csv_file: str):
        """
        Teste: Pipeline com diferentes colunas alvo
        
        Testa se a pipeline funciona mesmo quando a coluna alvo não existe
        (o sistema deve criar uma coluna simulada)
        """
        etl_page.log_step("=== TESTE: Coluna alvo diferente ===")
        
        etl_page.load_page()
        etl_page.upload_file(sample_csv_file)
        
        # Configurar com coluna alvo que não existe no arquivo
        etl_page.configure_pipeline(
            mode="train",
            target_column="score_personalizado",  # Coluna que não existe
            enable_enrichment=False
        )
        
        etl_page.execute_pipeline()
        etl_page.wait_for_pipeline_completion(timeout=120000)
        
        # Pipeline deve ter executado com sucesso mesmo assim
        results = etl_page.verify_results_displayed()
        assert int(results['total_records']) > 0
        
    def test_enrichment_enabled(self, etl_page: ETLPage, sample_csv_file: str):
        """
        Teste: Pipeline com enriquecimento habilitado
        
        Testa o processo com enriquecimento de dados via APIs externas
        """
        etl_page.log_step("=== TESTE: Pipeline com enriquecimento ===")
        
        etl_page.load_page()
        etl_page.upload_file(sample_csv_file)
        
        etl_page.configure_pipeline(
            mode="train",
            target_column="qualidade_lead",
            enable_enrichment=True  # Habilitar enriquecimento
        )
        
        etl_page.execute_pipeline()
        etl_page.wait_for_pipeline_completion(timeout=180000)  # Mais tempo para enriquecimento
        
        results = etl_page.verify_results_displayed()
        assert int(results['total_records']) > 0
        
        # Com enriquecimento, pode haver mais features
        features_count = int(results['features_created'])
        assert features_count >= 0


@pytest.mark.regression
@pytest.mark.ui
class TestUserInterface:
    """Testes da interface durante execução"""
    
    def test_progress_indication(self, etl_page: ETLPage, sample_csv_file: str):
        """
        Teste: Indicação de progresso funciona corretamente
        
        Verifica:
        - Barra de progresso aparece
        - Mensagens de status são atualizadas  
        - Progresso chega a 100%
        - Interface é atualizada corretamente
        """
        etl_page.log_step("=== TESTE: Indicação de progresso ===")
        
        etl_page.load_page()
        etl_page.upload_file(sample_csv_file)
        etl_page.configure_pipeline()
        
        # Executar pipeline
        etl_page.execute_pipeline()
        
        # Verificar que progresso apareceu
        etl_page.verify_element_visible(etl_page.SELECTORS['progress_container'])
        
        # Verificar que botão foi desabilitado durante execução
        # (Nota: Pode precisar verificar rapidamente antes da conclusão)
        
        # Aguardar conclusão
        etl_page.wait_for_pipeline_completion()
        
        # Verificar que interface voltou ao normal
        etl_page.verify_element_enabled(etl_page.SELECTORS['execute_btn'])
        etl_page.verify_element_visible(etl_page.SELECTORS['export_btn'])
        
    def test_notifications_display(self, etl_page: ETLPage, sample_csv_file: str):
        """
        Teste: Notificações são exibidas corretamente
        
        Verifica as diferentes notificações durante o fluxo:
        - Upload bem sucedido
        - Pipeline iniciada
        - Pipeline concluída
        - Download realizado
        """
        etl_page.log_step("=== TESTE: Sistema de notificações ===")
        
        etl_page.load_page()
        
        # Upload deve mostrar notificação
        etl_page.upload_file(sample_csv_file)
        # (Notificação já é verificada no método upload_file)
        
        # Configurar e executar
        etl_page.configure_pipeline()
        etl_page.execute_pipeline()
        # (Notificação de início já é verificada no método execute_pipeline)
        
        etl_page.wait_for_pipeline_completion()
        # (Notificação de conclusão já é verificada no método wait_for_completion)
        
        # Download deve mostrar notificação
        etl_page.export_results()
        # (Notificação de download já é verificada no método export_results)
        
        etl_page.log_assertion("Sistema de notificações funcionando corretamente")


@pytest.mark.regression  
@pytest.mark.slow
class TestLiveDashboard:
    """Testes do dashboard ao vivo"""
    
    def test_live_dashboard_during_execution(self, etl_page: ETLPage, sample_csv_file: str):
        """
        Teste: Dashboard ao vivo durante execução da pipeline
        
        Verifica:
        - Dashboard pode ser ativado
        - Métricas são atualizadas durante execução
        - Log de atividades é atualizado
        """
        etl_page.log_step("=== TESTE: Dashboard ao vivo durante execução ===")
        
        etl_page.load_page()
        
        # Ativar dashboard ao vivo
        etl_page.toggle_live_dashboard()
        
        # Configurar e iniciar pipeline
        etl_page.upload_file(sample_csv_file)
        etl_page.configure_pipeline()
        etl_page.execute_pipeline()
        
        # Durante a execução, verificar métricas
        etl_page.verify_live_metrics_updating(duration=5)
        etl_page.verify_activity_log_updates()
        
        # Aguardar conclusão
        etl_page.wait_for_pipeline_completion()
        
        # Verificar que métricas refletem a conclusão
        completed_today = etl_page.get_text(etl_page.SELECTORS['live_completed_today'])
        assert int(completed_today) >= 1, "Contador de concluídos deve ter aumentado"
        
        etl_page.log_assertion("Dashboard ao vivo funcionou durante execução")
