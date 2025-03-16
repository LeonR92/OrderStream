# First, stop all running containers (if any)
docker-compose down

# Start everything in the correct order
docker-compose up -d zookeeper
sleep 5

docker-compose up -d kafka1 kafka2 kafka3
sleep 10

docker-compose up -d kafka-init
sleep 5  

docker-compose up -d postgres
sleep 10

# Build and start the Flask backend and Kafka consumer
docker-compose up  --build flask-backend kafka-consumer

sleep 10

# Check if all services are running
docker-compose ps

docker-compose up -d kafka-ui
