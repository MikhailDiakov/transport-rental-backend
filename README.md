# 🚗 Car Rental Microservices System

A full-featured **Car Rental Platform** built using a modern **Microservices Architecture** powered by **FastAPI**.

---

## 📄 Service Details

Each microservice includes its own `README.md` file with:

- Overview of responsibilities
- Technologies used
- API endpoints and gRPC integration
- Kafka topic usage
- Testing instructions

---

## 🐳 Fully Dockerized

All services are fully containerized using **Docker** and orchestrated with **Docker Compose**.  
Environments are reproducible and isolated, supporting development, testing, and production.

---

## 🔭 Monitoring & Observability

- 📈 **Prometheus** + **Grafana** for metrics and service monitoring
- 📦 Centralized logs via **Kafka → Elasticsearch + Kibana**
- 🛠️ Health checks and metrics exposed by each service

---

## 🐳 Docker Compose Environments

### 🔧 Development

```bash
docker-compose -f docker-compose.dev.yml up --build
```

Lightweight setup for local development.

### 🧪 Testing

```bash
docker-compose -f docker-compose.test.yml up --build
```

Runs isolated test containers with pytest.

### 🚀 Full System

```bash
docker-compose -f docker-compose.yml up --build
```

Full-featured environment including Kafka, Redis, Prometheus, Grafana, etc.

---

## ⚙️ Environment Setup

- Fill in the `.env` and `.env.dev` files for each service with the required environment variables

---

## 👨‍💻 Author

Made with ❤️ and gRPC by Mykhailo Diakov

---
