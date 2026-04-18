# Revisor de Margens Inovatta

Aplicação web para análise e sugestão de margens por produto, com classificação de Curva ABC.

## Arquitetura

- **Frontend**: Streamlit (Streamlit Community Cloud)
- **Backend**: FastAPI (Google Cloud Run)
- **Storage**: Google Cloud Storage

## Pré-requisitos

- Python 3.12+
- Google Cloud SDK (`gcloud`)
- Conta GCP: linharedu@gmail.com

---

## 1. Configuração do GCP

```bash
# Criar novo projeto
gcloud projects create inovatta-revisor-margens --name="Inovatta Revisor Margens"
gcloud config set project inovatta-revisor-margens

# Vincular billing account (obrigatório para Cloud Run)
# Acesse: https://console.cloud.google.com/billing

# Habilitar APIs necessárias
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com \
  storage.googleapis.com \
  iam.googleapis.com

# Criar bucket GCS
gsutil mb -p inovatta-revisor-margens -c STANDARD -l us-central1 \
  gs://revisor-margens-inovatta

# Configurar lifecycle (auto-delete após 90 dias)
gsutil lifecycle set - gs://revisor-margens-inovatta <<EOF
{"rule": [{"action": {"type": "Delete"}, "condition": {"age": 90}}]}
EOF
```

### Permissões para o Cloud Run

```bash
# Obter email do service account padrão do Cloud Run
export SA="$(gcloud iam service-accounts list \
  --filter='displayName:Compute Engine default' \
  --format='value(email)')"

# Conceder acesso ao bucket
gsutil iam ch serviceAccount:${SA}:roles/storage.objectAdmin \
  gs://revisor-margens-inovatta

# Permitir geração de signed URLs
gcloud iam service-accounts add-iam-policy-binding ${SA} \
  --member="serviceAccount:${SA}" \
  --role="roles/iam.serviceAccountTokenCreator" \
  --project inovatta-revisor-margens
```

---

## 2. Deploy do Backend (Cloud Run)

```bash
# Build e push da imagem
gcloud builds submit ./backend \
  --tag gcr.io/inovatta-revisor-margens/revisor-margens-api:latest \
  --project inovatta-revisor-margens

# Deploy no Cloud Run
gcloud run deploy revisor-margens-api \
  --image gcr.io/inovatta-revisor-margens/revisor-margens-api:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 5 \
  --project inovatta-revisor-margens

# Obter a URL do serviço
gcloud run services describe revisor-margens-api \
  --region us-central1 \
  --format "value(status.url)" \
  --project inovatta-revisor-margens
```

---

## 3. Deploy do Frontend (Streamlit Community Cloud)

1. Faça push deste repositório para o GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io) e crie um novo app
3. Aponte para `frontend/app.py`
4. Adicione o secret `BACKEND_URL` com a URL do Cloud Run:

```toml
# Secrets no painel do Streamlit Community Cloud
BACKEND_URL = "https://revisor-margens-api-xxxxxxxx-uc.a.run.app"
```

---

## 4. Desenvolvimento Local

```bash
# Backend
cd backend
pip install -r requirements.txt
BACKEND_URL=http://localhost:8080 uvicorn main:app --reload --port 8080

# Frontend (em outro terminal)
cd frontend
pip install -r requirements.txt
BACKEND_URL=http://localhost:8080 streamlit run app.py

# Testes
pip install pytest
pytest tests/ -v
```

---

## Formato do Arquivo Excel

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| Código do Produto | texto | Identificador único |
| Produto | texto | Descrição do produto |
| Venda (R$) | número | Valor de vendas |
| Margem Atual | número | Margem em % (ex: 18.5 = 18,5%) |
