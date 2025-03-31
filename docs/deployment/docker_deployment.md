# Docker Deployment Guide for Metis_RAG

This guide explains how to deploy the Metis_RAG system using Docker and Docker Compose.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (version 20.10.0 or higher)
- [Docker Compose](https://docs.docker.com/compose/install/) (version 2.0.0 or higher)
- At least 8GB of RAM and 20GB of disk space

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Metis_RAG.git
   cd Metis_RAG
   ```

2. Copy the Docker environment file:
   ```bash
   cp config/.env.docker config/.env
   ```

3. Start the services:
   ```bash
   cd config
   docker-compose up -d
   ```

4. Access the application at http://localhost:8000

## Services

The Docker Compose configuration includes the following services:

- **metis-rag**: The main application
- **postgres**: PostgreSQL database for storing documents, conversations, and analytics
- **ollama**: Local LLM service for text generation and embeddings
- **mem0**: Memory layer for enhanced context in conversations

## Configuration

### Environment Variables

You can customize the deployment by modifying the environment variables in the `.env` file. The most important variables are:

- `METIS_PORT`: The port to expose the application on (default: 8000)
- `METIS_POSTGRES_PASSWORD`: The password for the PostgreSQL database
- `DEFAULT_MODEL`: The default LLM model to use (default: gemma3:4b)

### Volumes

The following volumes are used for data persistence:

- `postgres-data`: PostgreSQL data
- `../data/ollama`: Ollama models and data
- `../data/mem0`: Mem0 data
- `../data`: Application data (uploads, vector store, cache)

## Scaling

### Resource Requirements

- **Small deployment**: 8GB RAM, 4 CPU cores, 20GB disk
- **Medium deployment**: 16GB RAM, 8 CPU cores, 50GB disk
- **Large deployment**: 32GB RAM, 16 CPU cores, 100GB disk

### Performance Tuning

For better performance, you can adjust the following settings:

1. Increase PostgreSQL connection pool size in `.env`:
   ```
   DATABASE_POOL_SIZE=10
   DATABASE_MAX_OVERFLOW=20
   ```

2. Adjust the number of workers in the Docker Compose file:
   ```yaml
   metis-rag:
     # ...
     command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
   ```

## Monitoring

The Docker Compose configuration includes health checks for all services. You can monitor the health of the services using:

```bash
docker-compose ps
```

For more detailed monitoring, you can check the logs:

```bash
docker-compose logs -f
```

## Backup and Restore

### Database Backup

```bash
docker exec metis-postgres pg_dump -U postgres metis_rag > backup.sql
```

### Database Restore

```bash
cat backup.sql | docker exec -i metis-postgres psql -U postgres metis_rag
```

## Troubleshooting

### Common Issues

1. **Service fails to start**: Check the logs with `docker-compose logs <service-name>`
2. **Database connection issues**: Ensure PostgreSQL is running and the connection string is correct
3. **Out of memory errors**: Increase the memory allocated to Docker

### Logs

To view logs for a specific service:

```bash
docker-compose logs -f metis-rag
```

## Updating

To update to a new version:

1. Pull the latest changes:
   ```bash
   git pull
   ```

2. Rebuild and restart the services:
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

## Security Considerations

1. Change default passwords in the `.env` file
2. Use a reverse proxy (like Nginx) with HTTPS for production deployments
3. Restrict access to the Docker API
4. Regularly update all components

## Production Deployment

For production deployments, additional steps are recommended:

1. Use a dedicated PostgreSQL server with proper backup procedures
2. Set up a load balancer for high availability
3. Configure proper logging and monitoring
4. Use Docker Swarm or Kubernetes for orchestration