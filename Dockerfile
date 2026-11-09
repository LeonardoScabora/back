FROM maven:3.9-eclipse-temurin-21-alpine AS build

WORKDIR /app

COPY pom.xml ./
COPY src ./src

RUN mvn -B -DskipTests package

FROM eclipse-temurin:21-jdk-alpine

WORKDIR /app

RUN apk add --no-cache g++ python3

COPY --from=build /app/target/back-0.0.1-SNAPSHOT.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
