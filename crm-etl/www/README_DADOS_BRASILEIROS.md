# Compatibilidade com Dados Brasileiros

Este documento descreve as funcionalidades específicas implementadas para trabalhar com dados brasileiros no sistema de CRM.

## 📋 Funcionalidades Implementadas

### 1. **Validação de Telefones/WhatsApp Brasileiros**

O sistema aceita e valida telefones brasileiros em múltiplos formatos:

✅ **Formatos Aceitos:**
- `+55 (11) 99999-9999` - Formato completo internacional
- `(11) 99999-9999` - Formato com DDD
- `+55 11 99999-9999` - Formato com espaços
- `+5511999999999` - Formato compacto internacional
- `11 99999-9999` - Formato com espaço
- `11999999999` - Formato compacto
- `5511999999999` - Com código país sem +
- `(21) 3333-4444` - Telefone fixo

✅ **Features Extraídas:**
- `telefone_valido` - Se o telefone está em formato válido brasileiro
- `telefone_celular` - Se é número de celular (9º dígito = 9)
- `telefone_tem_codigo_pais` - Se contém código +55
- Formatação automática para padrão `+55 (XX) 9XXXX-XXXX`

### 2. **Validação de CPF e CNPJ**

Implementa os algoritmos oficiais de validação brasileiros:

✅ **CPF:**
- Valida dígitos verificadores
- Rejeita sequências inválidas (111.111.111-11)
- Aceita formatos com ou sem pontuação

✅ **CNPJ:**
- Valida dígitos verificadores usando algoritmo oficial
- Rejeita sequências inválidas
- Aceita formatos: `12.345.678/0001-90` ou `12345678000190`

### 3. **Formatação Monetária em Real (R$)**

✅ **Formatação Automática:**
- Converte valores para formato brasileiro: `R$ 1.234,56`
- Suporta entrada em múltiplos formatos
- Trata valores nulos apropriadamente
- Usa locale brasileiro quando disponível

✅ **Exemplos:**
```python
1234.56 → "R$ 1.234,56"
1000000 → "R$ 1.000.000,00"
"1234,56" → "R$ 1.234,56"
```

### 4. **Normalização de Nomes com Acentos**

✅ **Funcionalidades:**
- Preserva acentuação brasileira (á, é, í, ó, ú, ã, õ, ç)
- Capitaliza primeira letra de cada palavra
- Mantém preposições em minúscula (`de`, `da`, `do`, `das`, `dos`)
- Remove espaços extras

✅ **Exemplos:**
```
"josé DA silva" → "José da Silva"
"MARIA josé SANTOS" → "Maria José Santos"
"joão paulo DE oliveira" → "João Paulo de Oliveira"
```

## 🚀 Como Usar

### 1. **Gerar Dataset de Teste Brasileiro**

```bash
# Gera 100 registros brasileiros
python create_brazilian_dataset.py -o dados_brasileiros.csv -s 100

# Com formatação automática
python create_brazilian_dataset.py -o dados_brasileiros.csv -s 100 --format-phones --format-currency
```

### 2. **Processar Dados com Validações Brasileiras**

```bash
# ETL com validações brasileiras
python backend/unificado.py --mode etl --input dados_brasileiros.csv --output processados.csv

# Treinamento com dados brasileiros
python backend/unificado.py --mode train --input dados_brasileiros.csv --target qualidade_lead

# Predição em dados brasileiros
python backend/unificado.py --mode predict --input novos_dados.csv --output predicoes.csv
```

### 3. **Usar em Código Python**

```python
from backend.brazilian_utils import BrazilianDataValidator

# Validar telefone
valido = BrazilianDataValidator.validate_phone_whatsapp("+55 (11) 99999-9999")
formatado = BrazilianDataValidator.format_phone_whatsapp("11999999999")

# Validar CNPJ
cnpj_ok = BrazilianDataValidator.validate_cnpj("12.345.678/0001-90")

# Formatar moeda
valor_formatado = BrazilianDataValidator.format_currency_brl(1234.56)

# Normalizar nome
nome_normalizado = BrazilianDataValidator.normalize_name("josé DA silva")
```

## 📊 Dataset de Teste Brasileiro

O sistema inclui um gerador de dataset com dados brasileiros realistas:

✅ **Conteúdo Gerado:**
- **Nomes:** Brasileiros com acentuação correta
- **Cidades:** 20 principais cidades brasileiras
- **Estados:** Códigos de estado brasileiros (SP, RJ, MG, etc.)
- **CNPJs:** Válidos usando algoritmo oficial
- **Telefones:** Formatos regionais com DDDs corretos
- **Emails:** Domínios .com.br
- **Receitas:** Valores em Real brasileiro

✅ **Estrutura do Dataset:**
```
id, nome, email, telefone, whatsapp, cidade, estado, cnpj, 
empresa, cargo, receita_anual, data_contato, qualidade_lead
```

## 🧪 Testes e Validação

### Executar Testes

```bash
# Testes das funcionalidades brasileiras
python tests/test_brazilian_compatibility.py

# Exemplo prático completo
python exemplo_dados_brasileiros.py
```

### Verificar Qualidade dos Dados

O sistema calcula automaticamente um `data_quality_score` que considera:
- Email válido (+1)
- LinkedIn presente (+1)
- Telefone/WhatsApp válido (+1)
- CPF válido (+1)
- CNPJ válido (+1)
- Nome com mais de 5 caracteres (+1)

**Score máximo:** 6 pontos

## 📈 Estatísticas de Validação

Após o processamento, o sistema fornece estatísticas como:

```
=== Estatísticas de Validação ===
Telefones válidos: 45/50 (90.0%)
CNPJs válidos: 30/30 (100.0%)
CPFs válidos: 0/50 (0.0%)
Score médio de qualidade: 4.2/6
```

## 🔧 Configurações Avançadas

### Features Extraídas Automaticamente

Para cada coluna de telefone, o sistema cria:
- `{coluna}_valido` - Telefone em formato brasileiro válido
- `{coluna}_celular` - É número de celular
- `{coluna}_tem_codigo_pais` - Contém código +55

### Colunas de Receita

Detecta automaticamente colunas com valores monetários e cria versões formatadas em R$.

## 🎯 Casos de Uso

### 1. **CRM B2B Brasileiro**
- Validação automática de CNPJs de empresas
- Formatação padronizada de telefones
- Normalização de nomes de contatos

### 2. **Sistema de Leads**
- Score de qualidade baseado em validações brasileiras
- Detecção de telefones celulares para WhatsApp
- Formatação de valores de receita

### 3. **Análise de Dados**
- Limpeza automática de dados brasileiros
- Features engineeradas para ML
- Relatórios com formatação brasileira

## 🚨 Limitações e Considerações

1. **API ReceitaWS:** Desabilitada por padrão para evitar rate limiting
2. **Locale:** Formatação monetária pode variar conforme sistema operacional
3. **Performance:** Validações são executadas em série (otimizar para datasets muito grandes)

## 🔄 Roadmap Futuro

- [ ] Validação de CEP brasileiro
- [ ] Integração com API dos Correios
- [ ] Detecção automática de operadoras telefônicas
- [ ] Validação de dados bancários (conta/agência)
- [ ] Análise de DDD para localização geográfica

---

**Status da Implementação:** ✅ **Concluído**

Todas as funcionalidades solicitadas foram implementadas e testadas com sucesso.
