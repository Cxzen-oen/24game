# syntax=docker/dockerfile:1
# 前端构建
FROM node:22-alpine AS web
ENV NODE_OPTIONS=--max-old-space-size=512
WORKDIR /web
COPY demo/web/package.json demo/web/package-lock.json ./
RUN npm ci
COPY demo/web/ ./
RUN npm run build

# 后端构建（前端产物打进 Spring Boot 静态目录）
FROM maven:3.9-eclipse-temurin-21 AS server
ENV MAVEN_OPTS=-Xmx512m
WORKDIR /src
COPY demo/server/pom.xml ./
COPY demo/server/src ./src
COPY --from=web /web/dist ./src/main/resources/static
RUN mvn -B -q -DskipTests package

# 运行时
FROM eclipse-temurin:21-jre-alpine
RUN addgroup -S app && adduser -S -G app app
WORKDIR /app
COPY --from=server /src/target/game24-demo.jar app.jar
USER app
EXPOSE 8080
ENV TZ=UTC \
    JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=75 -XX:+ExitOnOutOfMemoryError -Duser.timezone=UTC"
ENTRYPOINT ["java", "-jar", "app.jar"]
