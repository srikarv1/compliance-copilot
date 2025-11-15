# Compliance Copilot for Banks

A production-ready AI-powered compliance analysis system built with LangChain, LangGraph, and a multi-agent architecture. Designed for financial institutions like BNY Mellon, JPMorgan, Goldman Sachs, Visa, and Stripe.

## 🏗️ Architecture

### Multi-Agent System
- **Retriever Agent (RAG)**: Retrieves relevant regulatory documents from vector database
- **Policy Extraction Agent**: Extracts specific policies and regulations from context
- **Risk Classification Agent**: Classifies risk levels and identifies violations
- **Hallucination Guard Agent**: Verifies facts against source documents
- **Supervisor Agent (LangGraph)**: Orchestrates the workflow using LangGraph state machine

### Tech Stack
- **Backend**: Python, FastAPI, LangChain, LangGraph, ChromaDB
- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Infrastructure**: Kubernetes, Terraform, Docker
- **Deployment**: Vercel (Frontend), Kubernetes (Backend)

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Kubernetes cluster (for production deployment)
- Terraform 1.0+
- OpenAI API key

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo>
cd agent
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local and set NEXT_PUBLIC_API_URL
```

### 4. Run with Docker Compose

```bash
# From project root
docker-compose up --build
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📦 Deployment

### Option 1: Deploy Frontend to Vercel

1. **Push your code to GitHub**

2. **Connect to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Set root directory to `frontend`
   - Add environment variable: `NEXT_PUBLIC_API_URL` (your backend API URL)

3. **Deploy**:
   ```bash
   cd frontend
   vercel --prod
   ```

### Option 2: Deploy to Kubernetes with Terraform

#### Step 1: Build and Push Docker Images

```bash
# Build backend image
cd backend
docker build -t your-registry/compliance-copilot-backend:latest .
docker push your-registry/compliance-copilot-backend:latest

# Build frontend image
cd ../frontend
docker build -t your-registry/compliance-copilot-frontend:latest .
docker push your-registry/compliance-copilot-frontend:latest
```

#### Step 2: Configure Terraform

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

Edit `terraform.tfvars`:
```hcl
kubeconfig_path   = "~/.kube/config"
kube_context      = "your-k8s-context"
openai_api_key    = "your-openai-api-key"
container_registry = "your-registry.io"
image_tag         = "latest"
backend_replicas  = 3
frontend_replicas = 2
```

#### Step 3: Deploy with Terraform

```bash
terraform init
terraform plan
terraform apply
```

#### Step 4: Get Service Endpoints

```bash
terraform output
```

### Option 3: Manual Kubernetes Deployment

```bash
# Create namespace
kubectl create namespace compliance-copilot

# Create secret
kubectl create secret generic compliance-secrets \
  --from-literal=openai-api-key=YOUR_KEY \
  -n compliance-copilot

# Apply manifests
kubectl apply -f kubernetes/pvc.yaml
kubectl apply -f kubernetes/backend-deployment.yaml
kubectl apply -f kubernetes/frontend-deployment.yaml

# Check status
kubectl get pods -n compliance-copilot
kubectl get services -n compliance-copilot
```

## 🔧 Configuration

### Backend Environment Variables

```env
OPENAI_API_KEY=your_key_here
CHROMA_PERSIST_DIRECTORY=./chroma_db
PORT=8000
ENVIRONMENT=production
```

### Frontend Environment Variables

```env
NEXT_PUBLIC_API_URL=http://your-backend-url:8000
```

## 📚 Usage

### 1. Upload Documents

Upload regulatory PDFs, internal policies, or audit logs through the UI or API:

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@regulation.pdf"
```

### 2. Analyze Compliance

Use the UI or API to analyze compliance:

```bash
curl -X POST http://localhost:8000/api/compliance/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Does this transaction violate AML regulations?",
    "transaction_data": {
      "type": "Wire Transfer",
      "amount": "$50,000",
      "region": "US",
      "customer_type": "Corporate"
    }
  }'
```

## 🏛️ Project Structure

```
agent/
├── backend/
│   ├── agents/
│   │   ├── retriever_agent.py
│   │   ├── policy_extraction_agent.py
│   │   ├── risk_classification_agent.py
│   │   ├── hallucination_guard_agent.py
│   │   └── supervisor_agent.py
│   ├── vector_store.py
│   ├── config.py
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   ├── components/
│   ├── package.json
│   └── Dockerfile
├── kubernetes/
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   ├── pvc.yaml
│   └── secrets.yaml
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── docker-compose.yml
└── README.md
```

## 🧪 Testing

### Backend API Health Check

```bash
curl http://localhost:8000/health
```

### Test Document Search

```bash
curl "http://localhost:8000/api/documents/search?query=AML%20regulations&k=5"
```

## 🔒 Security Considerations

- Store API keys in Kubernetes secrets (not in code)
- Use environment variables for sensitive data
- Enable CORS only for trusted domains in production
- Use HTTPS in production
- Implement authentication/authorization for production use

## 📊 Monitoring

### Kubernetes Monitoring

```bash
# View logs
kubectl logs -f deployment/compliance-copilot-backend -n compliance-copilot

# Check resource usage
kubectl top pods -n compliance-copilot
```

## 🚧 Production Checklist

- [ ] Set up proper authentication/authorization
- [ ] Configure HTTPS/TLS certificates
- [ ] Set up monitoring and logging (Prometheus, Grafana)
- [ ] Configure backup for ChromaDB data
- [ ] Set up CI/CD pipeline
- [ ] Configure auto-scaling
- [ ] Set up alerting
- [ ] Review and harden security settings
- [ ] Load testing
- [ ] Disaster recovery plan

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

MIT License

## 🎯 Resume Points

- Built production-ready multi-agent AI system using LangChain and LangGraph
- Implemented RAG pipeline with ChromaDB for regulatory document retrieval
- Designed and deployed scalable microservices architecture on Kubernetes
- Automated infrastructure provisioning using Terraform
- Created modern React/Next.js frontend deployed on Vercel
- Implemented fact-checking agent to prevent AI hallucinations
- Built compliance analysis system handling 1000s of regulatory documents

## 📞 Support

For issues and questions, please open an issue on GitHub.

