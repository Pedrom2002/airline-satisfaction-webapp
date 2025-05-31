# Flight Satisfaction Predictor

Um aplicativo web em Flask para prever a satisfação de passageiros em voos, integrado com métricas, visualizações interativas e histórico de predições.
Utilizado o modelo criado por mim que esta disponivel nesta repo: [https://github.com/Pedrom2002/Airline-Passenger-Satisfaction]

## Demo ao Vivo  
Acesse a aplicação em: [https://airline-satisfaction-webapp.onrender.com]
Demora a abrir pois esta hospedado no Render,plano gratuito logo o mesmo suspende o website quando nao é acessado regularmente.


---

## 🛠️ Tecnologias

- **Python 3.10+**
- **Flask** (Blueprints, Application Factory)
- **scikit-learn**, **pandas**, **numpy** para ML e pré-processamento
- **Plotly** para gráficos interativos
- **Tailwind CSS** para estilos modernos e responsivos
- **DataTables** para tabelas com filtros e paginação
- **SQLite** (facilmente migrável para PostgreSQL)

---

## 📦 Dependências

Todas as bibliotecas utilizadas neste projeto estão listadas em `requirements.txt`. Principais:

```
Flask==3.1.1
Flask-Limiter==3.12
flask-talisman==1.1.0
Flask-SQLAlchemy==3.1.1
Flask-WTF==1.2.2
flask-restx==1.3.0
flasgger==0.9.7.1

numpy==2.2.6
pandas==2.2.3
scikit-learn==1.6.1
xgboost==3.0.2

plotly==6.1.1
matplotlib==3.10.3

python-dotenv==1.1.0

pytest==8.3.5
pytest-flask==1.3.0
pytest-cov==6.1.1
```

Para instalar todas:
```bash
pip install -r requirements.txt
```



---

## 🚀 Como Rodar Localmente

1. Abra o terminal e clone o repositório:
   git clone https://github.com/Pedrom2002/airline-satisfaction-webapp
   cd airline-satisfaction.webapp
   
2. Crie e ative um ambiente virtual(preferivel):
   python -m venv .venv
   .\.venv\Scripts\activate   # Windows
   source .venv/bin/activate  # Linux/macOS
   
3. Instale as dependências:
   pip install -r requirements.txt
   
4. Inicialize o banco de dados:
   flask db upgrade

5. Execute a aplicação:

   python -m flask run     
   
6. Acesse em `http://localhost:5000`

7.Para testar a pagina de admin criar um utilizador com o nome "test"
---

## 🏗️ Estrutura de Pastas

```
flight-satisfaction-app/
├── app/
│   ├── __init__.py         # Application Factory
│   ├── auth/               # Blueprint de autenticação (login, registro)
│   ├── admin/              # Blueprint de administração
│   ├── prediction/         # Blueprint de predição e históric
│   │── eda.py              # Funções de EDA e pré-processamento
│   │── model.py            # Carregamento e inferência do modelo
│   ├── static/             # CSS, JS, assets
│   └── templates/          # Templates Jinja2
├── static/                 # CSS, JS, assets
├── docs/                   # Diagramas, capturas, documentação extra
├── tests/                  # Testes unitários e integrados
├── requirements.txt        # Dependências
├── run.py                  # Entrypoint da aplicação
└── README.md               # Este arquivo
```

---

## 📝 Uso da Aplicação

1. **Registro e Login**: Crie uma conta ou faça login para acessar funcionalidades.
2. **Upload de CSV**: Envie um arquivo CSV com os dados dos passageiros.
3. **Predição**: O sistema processa os dados, aplica o modelo pré-treinado e gera uma tabela com as predições.
4. **Visualizações**: Explore métricas de satisfação, histogramas, gráficos de pizza, clustering de perfis, etc.
5. **Histórico**: Acesse o histórico de predições anteriores.
6. **Download**: Baixe o CSV com as colunas originais e a predição em uma nova coluna.


## 📚 Documentação das Rotas

Veja `/docs/routes.md` para detalhes de cada endpoint, parâmetros e exemplos de uso.

---

## 📄 Documentação de Arquitetura

Diagramas e fluxos de dados estão em `docs/architecture/` (Mermaid, draw.io).

---

## 🧪 Testes

- Execute todos os testes:
  ```bash
  pytest --cov=app tests/
  ```
- Testes de rotas, modelos e utils estão em `tests/`.

---

## 🌐 Produção

- Configure variáveis de ambiente para produção (`FLASK_ENV=production`).
- Use um servidor WSGI (Gunicorn/uwsgi).
- Habilite HTTPS e variáveis de segurança.

---

## 📝 Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
