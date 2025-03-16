docker-compose down postgres
docker-compose up -d postgres
sleep 10
docker-compose up -d flask-backend