FROM eclipse-temurin:21-jdk-jammy AS build

WORKDIR /workspace/java-services/water-approval

COPY java-services/water-approval/.mvn .mvn
COPY java-services/water-approval/mvnw java-services/water-approval/pom.xml ./
RUN chmod +x mvnw && ./mvnw -B -DskipTests dependency:go-offline

COPY java-services/water-approval/src src
RUN ./mvnw -B -DskipTests package

FROM eclipse-temurin:21-jre-jammy

WORKDIR /app
ENV TZ=Asia/Shanghai

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system smartwater && useradd --system --gid smartwater smartwater
COPY --from=build /workspace/java-services/water-approval/target/*.jar /app/water-approval.jar

USER smartwater
EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/app/water-approval.jar"]
