# First, stop all running containers (if any)
docker-compose down

# Start everything in the correct order
docker-compose up -d zookeeper
sleep 5

docker-compose up -d kafka1 kafka2 kafka3
sleep 5

docker-compose up -d kafka-init
sleep 5  

docker-compose up -d postgres
sleep 5

# Build and start the Flask backend and Kafka consumer
docker-compose up  --build flask-backend kafka-consumer

sleep 8


docker-compose up -d kafka-ui
