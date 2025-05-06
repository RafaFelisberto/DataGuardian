# DataGuardian — Monitor Inteligente de Vazamento de Dados Pessoais

Projeto desenvolvido para detectar automaticamente **dados pessoais sensíveis** (como CPF, e-mail, senhas, entre outros) em arquivos como **CSV, JSON, TXT e SQL dumps**, ajudando na identificação proativa de possíveis vazamentos.

## 🔍 Funcionalidades Principais

- [x] Upload de arquivos (CSV, JSON, TXT, SQL)
- [x] Detecção automática de dados sensíveis usando **Regex + NLP**
- [x] Identificação de padrões suspeitos (ex: senhas em logs, chaves expostas)
- [x] Dashboard interativo com visualização dos riscos
- [ ] Sistema de alerta por e-mail (em desenvolvimento)
- [ ] Criptografia automática de campos críticos (em desenvolvimento)

## ⚙️ Tecnologias Utilizadas

- **Python 3.9+**
- **Streamlit** – Interface interativa
- **Pandas** – Processamento de dados
- **spaCy** – Análise de linguagem natural
- **Fernet (Cryptography)** – Criptografia de dados
- **Regex** – Detecção de padrões

## 🧪 Exemplos de Dados Sensíveis Detectados

O sistema consegue identificar automaticamente:

| Tipo de Dado | Exemplo |
|--------------|---------|
| CPF          | 123.456.789-09 |
| CNPJ         | 12.345.678/0001-90 |
| E-mail       | usuario@email.com |
| Senha        | A1b@3456 |
| Telefone     | (11) 99999-9999 |
| Cartão de Crédito | 5555 4444 3333 2222 |

Padrões baseados em expressões regulares e modelos de linguagem da biblioteca spaCy [[3]].

## 📦 Como Rodar o Projeto

### 1. Clone o repositório

```bash
git clone https://github.com/RafaFelisberto/DataGuardian.git
cd DataGuardian
