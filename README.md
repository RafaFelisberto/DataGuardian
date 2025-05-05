🛡️ DataGuardian
DataGuardian é uma ferramenta de código aberto para análise e detecção de dados sensíveis em arquivos de texto. Utilizando expressões regulares e técnicas de processamento de linguagem natural, o DataGuardian identifica informações como CPF, e-mails e senhas, auxiliando na prevenção de vazamentos de dados.

🚀 Funcionalidades
Detecção de dados sensíveis (CPF, e-mails, senhas) em arquivos de texto.

Análise de arquivos em formatos .txt e .csv.

Geração de relatórios resumidos com os dados encontrados.

Interface de linha de comando para facilidade de uso.

🧰 Tecnologias Utilizadas
Python 3.x

Bibliotecas: re, argparse, pandas

📦 Instalação
Clone o repositório:

bash
Copiar
Editar
git clone https://github.com/RafaFelisberto/DataGuardian.git
cd DataGuardian
Crie um ambiente virtual (opcional, mas recomendado):

bash
Copiar
Editar
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
Instale as dependências:

bash
Copiar
Editar
pip install -r requirements.txt
⚙️ Uso
Execute o script principal passando o caminho do arquivo a ser analisado:

bash
Copiar
Editar
python main.py --file caminho/do/arquivo.txt
O resultado será exibido no terminal, indicando as ocorrências de dados sensíveis encontradas.

📝 Exemplo
Suponha que você tenha um arquivo dados.txt com o seguinte conteúdo:

makefile
Copiar
Editar
Nome: João Silva
CPF: 123.456.789-00
Email: joao.silva@example.com
Senha: senha123
Executando:

bash
Copiar
Editar
python main.py --file dados.txt
Saída esperada:

yaml
Copiar
Editar
Dados sensíveis encontrados:
- CPF: 123.456.789-00
- Email: joao.silva@example.com
- Senha: senha123
📌 Contribuindo
Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

📄 Licença
Este projeto está licenciado sob a Licença MIT. Consulte o arquivo LICENSE para obter mais detalhes.

