# Flight Satisfaction Predictor

Um aplicativo web em Flask para prever a satisfação de passageiros em voos, integrado com métricas, visualizações interativas e histórico de predições.

---

## 🛠️ Tecnologias

- **Python 3.10+**
- **Flask** (Blueprints, Application Factory)
- **scikit-learn**, **pandas**, **numpy** para ML e pré-processamento
- **Plotly** para gráficos interativos
- **Tailwind CSS** para estilos modernos e responsivos
- **DataTables** para tabelas com filtros e paginação
- **SQLite** (facilmente migrável para PostgreSQL)

## 📸 Captura de Tela

![](docs/screenshot.png)

> Exemplo da página de resultados com métricas, gráficos interativos e botão de download.

---

## 🚀 Como Rodar Localmente

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/flight-satisfaction-app.git
   cd flight-satisfaction-app
   ```
2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .\.venv\Scripts\activate   # Windows
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Defina variáveis de ambiente (exemplo .env):
   ```ini
   FLASK_APP=run.py
   FLASK_ENV=development
   SECRET_KEY=uma-chave-secreta
   DATABASE_URL=sqlite:///data/app.db
   ```
5. Inicialize o banco de dados:
   ```bash
   flask db upgrade
   ```
6. Execute a aplicação:
   ```bash
   flask run
   ```
7. Acesse em `http://localhost:5000`

---

## 🏗️ Estrutura de Pastas

```
flight-satisfaction-app/
├── app/
│   ├── __init__.py         # Application Factory
│   ├── auth/               # Blueprint de autenticação (login, registro)
│   ├── admin/              # Blueprint de administração
│   ├── prediction/         # Blueprint de predição e histórico
│   ├── utils/
│   │   ├── eda.py          # Funções de EDA e pré-processamento
│   │   └── model.py        # Carregamento e inferência do modelo
│   ├── static/             # CSS, JS, assets
│   └── templates/          # Templates Jinja2
├── migrations/             # Versionamento do banco via Flask-Migrate
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

---

## 🔧 Treinamento do Modelo

Se quiser re-treinar ou ajustar o modelo:

1. Prepare um dataset no formato original (colunas: id, Gender, Customer Type, Age, Type of Travel, Class, Flight Distance, Inflight wifi service, Departure/Arrival time convenient, Ease of Online booking, Gate location, Food and drink, Online boarding, Seat comfort, Inflight entertainment, On-board service, Leg room service, Baggage handling, Checkin service, Inflight service, Cleanliness, Departure Delay in Minutes, Arrival Delay in Minutes, satisfaction).
2. Execute o script de treinamento:
   ```bash
   python scripts/train_model.py --input data/raw.csv --output app/utils/model.pkl
   ```
3. Atualize o arquivo `model.pkl` em `app/utils/`.

---

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
