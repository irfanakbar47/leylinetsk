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
   While you're in the leylinetsk directory, simply run the command below to build the necessary images and deploy the application using Docker Compose on port 3000.
   ```bash
   
   docker-compose up -d --build

4. **Running with kubernetes deployment**
   If you already have a Kubernetes cluster, you can deploy the application by running all the deployment files in the ./leylinetsk/kubernetes directory using the commands below, specifying the namespace where 
   you want your application to be deployed.
   ```bash
   kubectl apply -f postgres-pv.yaml
   kubectl apply -f postgres-pvc.yaml -n namespace
   kubectl apply -f db-secrets.yaml -n namespace
   kubectl apply -f init-db-configmap.yaml -n namespace
   kubectl apply -f fastapi-config.yaml -n namespace
   kubectl apply -f fastapi-deployment.yaml -n namespace
   kubectl apply -f fastapi-svc.yaml -n namespace
   kubectl apply -f postgres-deployment.yaml -n namespace
   kubectl apply -f postgres-svc.yaml -n namespace

6. **Running application as helm chart**
   First, install Helm, then navigate to the ./leylinetsk/kubernetes directory and run the commands below.
   ```bash
   helm package helm 
   helm install application-name application-package.tgz -n namespace

   and also create pv and pvc for the application by running below commands
   kubectl apply -f postgres-pv.yaml
   kubectl apply -f postgres-pvc.yaml -n namespace
   
