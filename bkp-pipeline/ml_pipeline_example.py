#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo de Pipeline de Machine Learning
Utilização dos dados processados para treinar modelos ML
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import cross_val_score
import json
import warnings
warnings.filterwarnings('ignore')

class MLPipelineExample:
    """
    Classe para demonstrar uso dos dados processados em pipelines ML
    """
    
    def __init__(self, data_dir='./ml_datasets/'):
        self.data_dir = data_dir
        self.X_train = None
        self.X_val = None
        self.X_test = None
        self.y_train = None
        self.y_val = None
        self.y_test = None
        self.metadata = None
        self.models = {}
        self.results = {}
    
    def load_processed_data(self):
        """
        Carrega os dados processados
        """
        print("Carregando dados processados...")
        
        # Carrega datasets
        self.X_train = pd.read_csv(f"{self.data_dir}X_train.csv")
        self.X_val = pd.read_csv(f"{self.data_dir}X_val.csv")
        self.X_test = pd.read_csv(f"{self.data_dir}X_test.csv")
        
        self.y_train = pd.read_csv(f"{self.data_dir}y_train.csv")['target'].values
        self.y_val = pd.read_csv(f"{self.data_dir}y_val.csv")['target'].values
        self.y_test = pd.read_csv(f"{self.data_dir}y_test.csv")['target'].values
        
        # Carrega metadados
        with open(f"{self.data_dir}metadata.json", 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        
        print(f"✅ Dados carregados:")
        print(f"   Treino: {self.X_train.shape}")
        print(f"   Validação: {self.X_val.shape}")
        print(f"   Teste: {self.X_test.shape}")
        print(f"   Features: {self.metadata['feature_names']}")
        
        return True
    
    def initialize_models(self):
        """
        Inicializa diferentes modelos para comparação
        """
        print("\nInicializando modelos...")
        
        self.models = {
            'RandomForest': RandomForestClassifier(
                n_estimators=100,
                max_depth=5,
                random_state=42,
                class_weight='balanced'
            ),
            'GradientBoosting': GradientBoostingClassifier(
                n_estimators=100,
                max_depth=3,
                random_state=42
            ),
            'LogisticRegression': LogisticRegression(
                random_state=42,
                class_weight='balanced',
                max_iter=1000
            ),
            'SVM': SVC(
                kernel='rbf',
                random_state=42,
                class_weight='balanced',
                probability=True
            )
        }
        
        print(f"✅ {len(self.models)} modelos inicializados")
        return self.models
    
    def train_and_evaluate_models(self):
        """
        Treina e avalia todos os modelos
        """
        print("\nTreinando e avaliando modelos...")
        print("=" * 50)
        
        for name, model in self.models.items():
            print(f"\n🤖 Treinando {name}...")
            
            try:
                # Treina o modelo
                model.fit(self.X_train, self.y_train)
                
                # Predições
                y_train_pred = model.predict(self.X_train)
                y_val_pred = model.predict(self.X_val)
                y_test_pred = model.predict(self.X_test)
                
                # Métricas
                train_acc = accuracy_score(self.y_train, y_train_pred)
                val_acc = accuracy_score(self.y_val, y_val_pred)
                test_acc = accuracy_score(self.y_test, y_test_pred)
                
                # Cross-validation
                cv_scores = cross_val_score(model, self.X_train, self.y_train, cv=3)
                
                # Armazena resultados
                self.results[name] = {
                    'model': model,
                    'train_accuracy': train_acc,
                    'val_accuracy': val_acc,
                    'test_accuracy': test_acc,
                    'cv_mean': cv_scores.mean(),
                    'cv_std': cv_scores.std(),
                    'y_test_pred': y_test_pred
                }
                
                print(f"   Acurácia Treino: {train_acc:.3f}")
                print(f"   Acurácia Validação: {val_acc:.3f}")
                print(f"   Acurácia Teste: {test_acc:.3f}")
                print(f"   CV Score: {cv_scores.mean():.3f} (±{cv_scores.std():.3f})")
                
            except Exception as e:
                print(f"   ❌ Erro ao treinar {name}: {e}")
        
        return self.results
    
    def analyze_feature_importance(self):
        """
        Analisa a importância das features
        """
        print("\n📊 Análise de Importância das Features")
        print("=" * 50)
        
        # Modelos que possuem feature_importances_
        tree_models = ['RandomForest', 'GradientBoosting']
        
        for model_name in tree_models:
            if model_name in self.results:
                model = self.results[model_name]['model']
                
                if hasattr(model, 'feature_importances_'):
                    importances = model.feature_importances_
                    feature_names = self.metadata['feature_names']
                    
                    # Cria DataFrame e ordena por importância
                    importance_df = pd.DataFrame({
                        'feature': feature_names,
                        'importance': importances
                    }).sort_values('importance', ascending=False)
                    
                    print(f"\n{model_name} - Top 5 Features:")
                    for idx, row in importance_df.head().iterrows():
                        print(f"  {row['feature']}: {row['importance']:.4f}")
    
    def generate_detailed_report(self):
        """
        Gera relatório detalhado dos resultados
        """
        print("\n📝 Gerando relatório detalhado...")
        
        report = []
        report.append("=" * 70)
        report.append("RELATÓRIO DE RESULTADOS - PIPELINE MACHINE LEARNING")
        report.append("=" * 70)
        report.append(f"Dataset: {self.metadata.get('processing_date', 'N/A')}")
        report.append(f"Total de features: {len(self.metadata['feature_names'])}")
        report.append(f"Amostras de treino: {self.X_train.shape[0]}")
        report.append(f"Amostras de teste: {self.X_test.shape[0]}")
        report.append("")
        
        # Resultados por modelo
        report.append("RESULTADOS POR MODELO:")
        report.append("-" * 40)
        
        # Ordena modelos por acurácia de validação
        sorted_results = sorted(self.results.items(), 
                               key=lambda x: x[1]['val_accuracy'], 
                               reverse=True)
        
        for i, (name, result) in enumerate(sorted_results, 1):
            report.append(f"{i}. {name}:")
            report.append(f"   Acurácia Treino: {result['train_accuracy']:.4f}")
            report.append(f"   Acurácia Validação: {result['val_accuracy']:.4f}")
            report.append(f"   Acurácia Teste: {result['test_accuracy']:.4f}")
            report.append(f"   CV Score: {result['cv_mean']:.4f} (±{result['cv_std']:.4f})")
            report.append("")
        
        # Melhor modelo
        best_model_name = sorted_results[0][0]
        best_result = sorted_results[0][1]
        
        report.append(f"MELHOR MODELO: {best_model_name}")
        report.append("-" * 40)
        report.append(f"Acurácia no conjunto de teste: {best_result['test_accuracy']:.4f}")
        report.append("")
        
        # Matriz de confusão do melhor modelo
        cm = confusion_matrix(self.y_test, best_result['y_test_pred'])
        report.append("MATRIZ DE CONFUSÃO (Melhor Modelo):")
        report.append(f"[[{cm[0,0]:2d}, {cm[0,1]:2d}]]")
        report.append(f"[[{cm[1,0]:2d}, {cm[1,1]:2d}]]")
        report.append("")
        
        # Relatório de classificação
        class_report = classification_report(self.y_test, best_result['y_test_pred'])
        report.append("RELATÓRIO DE CLASSIFICAÇÃO (Melhor Modelo):")
        report.append(class_report)
        
        # Features utilizadas
        report.append("FEATURES UTILIZADAS:")
        report.append("-" * 20)
        for i, feature in enumerate(self.metadata['feature_names'], 1):
            report.append(f"{i:2d}. {feature}")
        
        report.append("\n" + "=" * 70)
        
        report_text = "\n".join(report)
        
        # Salva relatório
        with open(f"{self.data_dir}ml_pipeline_results.txt", 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        return report_text
    
    def recommend_next_steps(self):
        """
        Recomenda próximos passos para otimização
        """
        print("\n🎯 Recomendações para Otimização")
        print("=" * 40)
        
        # Analisa performance
        best_val_acc = max(result['val_accuracy'] for result in self.results.values())
        
        recommendations = []
        
        if best_val_acc < 0.8:
            recommendations.append("• Coletar mais dados para melhorar a performance")
            recommendations.append("• Considerar feature engineering mais avançado")
        
        if len(self.X_train) < 100:
            recommendations.append("• Dataset pequeno - considerar técnicas de data augmentation")
            recommendations.append("• Usar modelos mais simples para evitar overfitting")
        
        # Verifica overfitting
        for name, result in self.results.items():
            train_val_diff = result['train_accuracy'] - result['val_accuracy']
            if train_val_diff > 0.1:
                recommendations.append(f"• {name} apresenta overfitting - ajustar regularização")
        
        recommendations.extend([
            "• Experimentar hyperparameter tuning com GridSearch/RandomSearch",
            "• Considerar ensemble methods",
            "• Aplicar técnicas de balanceamento de classes se necessário",
            "• Validar modelo com dados reais de produção"
        ])
        
        for rec in recommendations:
            print(rec)

def main():
    """
    Função principal para executar o pipeline completo
    """
    print("Iniciando Pipeline de Machine Learning")
    print("=" * 50)
    
    # Inicializa pipeline
    pipeline = MLPipelineExample()
    
    try:
        # 1. Carrega dados processados
        pipeline.load_processed_data()
        
        # 2. Inicializa modelos
        pipeline.initialize_models()
        
        # 3. Treina e avalia modelos
        pipeline.train_and_evaluate_models()
        
        # 4. Analisa importância das features
        pipeline.analyze_feature_importance()
        
        # 5. Gera relatório detalhado
        report = pipeline.generate_detailed_report()
        print("\n" + report)
        
        # 6. Recomendações
        pipeline.recommend_next_steps()
        
        print(f"\n✅ Pipeline concluído com sucesso!")
        print(f"📊 Relatório salvo em: {pipeline.data_dir}ml_pipeline_results.txt")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()

