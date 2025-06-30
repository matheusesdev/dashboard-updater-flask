# Atualizador de Dashboard VCA

Esta é uma aplicação web Flask projetada para sincronizar dados de uma planilha local (Excel ou CSV) com uma planilha do Google Sheets, atuando como um atualizador de dashboard.

## Funcionalidades

-   Interface web simples para upload de arquivos.
-   Suporte para arquivos `.xlsx`, `.xls` e `.csv`.
-   Comparação inteligente entre a planilha local e o Google Sheets.
-   **Atualiza** registros existentes no dashboard.
-   **Adiciona** novos registros que não existem no dashboard.
-   Gera um log detalhado do processo na interface.

## Como Executar o Projeto

Siga os passos abaixo para configurar e rodar a aplicação localmente.

### Pré-requisitos

-   Python 3.x
-   Conta de Serviço do Google Cloud com a API do Google Sheets e Google Drive ativadas.

### 1. Clonar o Repositório

```bash
git clone https://github.com/SEU-USUARIO/NOME-DO-SEU-REPO.git
cd NOME-DO-SEU-REPO
```

### 2. Criar e Ativar um Ambiente Virtual

```bash
# Para Windows
python -m venv venv
venv\Scripts\activate

# Para macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar as Dependências

As dependências estão listadas no arquivo `requirements.txt`.

```bash
pip install -r requirements.txt
```

*(Nota: Crie o `requirements.txt` com o comando `pip freeze > requirements.txt`)*

### 4. Configurar as Credenciais

**Esta é a etapa mais importante para a segurança!**

1.  **Credenciais do Google:**
    -   Obtenha o seu arquivo `credentials.json` do Google Cloud Console.
    -   Coloque este arquivo na pasta raiz do projeto.
    -   **IMPORTANTE:** O arquivo `credentials.json` está listado no `.gitignore` e **nunca** deve ser enviado para o repositório.
    -   Lembre-se de compartilhar o e-mail da sua conta de serviço com a planilha do Google Sheets que você deseja editar, dando a ele permissão de "Editor".

2.  **Variáveis de Ambiente:**
    -   Este projeto usa `python-dotenv` para gerenciar variáveis. Renomeie o arquivo `env.example` para `.env`. Por enquanto, este projeto não requer variáveis, mas é uma boa prática tê-lo pronto.

### 5. Executar a Aplicação

Com tudo configurado, inicie o servidor Flask:

```bash
python app.py
```

Acesse a aplicação no seu navegador em `http://127.0.0.1:5000`.