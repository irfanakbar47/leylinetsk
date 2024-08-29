## Getting Started

### Prerequisites

- Docker
- Kubernetes (Minikube or any Kubernetes cluster)
- Helm 3
- Python 3.9+

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/irfanakbar47/leylinetsk.git
   cd leylinetsk

2. **Running with docker-compose**
   ```bash
   while you are in leylinktsk dir, just need to run below command which will build required images and and deploy the application on docker-compose on port 3000 
   docker-compose up -d --build

3. **Running with kubernetes deployment**
   ```bash
   If you already have cluster run all the deployment files in ./leylinktsk/kubernetes dir with below commands with your namespace where you want your application 
   kubectl apply -f postgres-pv.yaml
   kubectl apply -f postgres-pvc.yaml -n namespace
   kubectl apply -f db-secrets.yaml -n namespace
   kubectl apply -f init-db-configmap.yaml -n namespace
   kubectl apply -f fastapi-config.yaml -n namespace
   kubectl apply -f fastapi-deployment.yaml -n namespace
   kubectl apply -f fastapi-svc.yaml -n namespace
   kubectl apply -f postgres-deployment.yaml -n namespace
   kubectl apply -f postgres-svc.yaml -n namespace

4. **Running application as helm chart**
   ```bash
   First need to install helm and then go to ./leylinktsk/kubernetes and run below commands
   helm package helm 
   helm install application-name application-package.tgz -n namespace

   and also create pv and pvc for the application by running below commands
   kubectl apply -f postgres-pv.yaml
   kubectl apply -f postgres-pvc.yaml -n namespace
   
