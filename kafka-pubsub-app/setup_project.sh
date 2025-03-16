#!/bin/bash

# Project Root
PROJECT_ROOT="kafka-pubsub-app"
mkdir -p $PROJECT_ROOT && cd $PROJECT_ROOT

# Backend (Flask API)
mkdir -p backend/app backend/tests
touch backend/{requirements.txt,run.py,Dockerfile}
touch backend/app/{__init__.py,routes.py,models.py,database.py,config.py,producer.py}
touch backend/tests/{test_routes.py,test_producer.py,test_models.py}

# Debezium (CDC)
mkdir -p debezium
touch debezium/{docker-compose.yml,connector-config.json}

# Kafka Cluster
mkdir -p kafka
touch kafka/{docker-compose.yml,topics.sh}
chmod +x kafka/topics.sh  # Make script executable

# Consumer Application
mkdir -p consumer_app/tests
touch consumer_app/{consumer.py,processor.py,database.py,config.py,requirements.txt,Dockerfile}
touch consumer_app/tests/{test_consumer.py,test_processor.py,test_database.py}

# Frontend (Flask for rendering)
mkdir -p frontend/static frontend/templates
touch frontend/{app.py,requirements.txt,Dockerfile}
touch frontend/static/{styles.css,script.js}
touch frontend/templates/index.html

# Root files
touch .env docker-compose.yml README.md

echo "✅ Project structure created successfully!"

