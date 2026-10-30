# Build the React website
FROM node:22-slim AS web
WORKDIR /build/frontend
COPY frontend/package.json ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# Build the Spring Boot server with the website inside it
FROM maven:3.9-eclipse-temurin-21 AS api
WORKDIR /build
COPY backend/pom.xml ./
COPY backend/src ./src
COPY --from=web /build/backend/src/main/resources/static ./src/main/resources/static
RUN mvn -q -B -DskipTests package

# Run Spring Boot, the Python ML service and PostgreSQL together
FROM eclipse-temurin:21-jre-noble
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql python3 python3-venv libgomp1 \
    && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 app
WORKDIR /app
COPY ml-service/app.py ml-service/lookalike_check.py ml-service/url_feature_extractor.py ml-service/requirements.txt ./ml-service/
COPY models/xgboost_url.json models/known_sites.txt ./models/
COPY --from=api /build/target/backend-1.0.0.jar ./app.jar
COPY docker/start.sh ./start.sh
RUN sed -i 's/\r$//' start.sh && chmod +x start.sh
RUN python3 -m venv /app/venv && /app/venv/bin/pip install --no-cache-dir -r ml-service/requirements.txt
RUN chown -R app:app /app
USER app
EXPOSE 7860
CMD ["/app/start.sh"]
