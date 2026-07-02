
plugins {
    java
    id("org.springframework.boot") version "3.4.1"
    id("io.spring.dependency-management") version "1.1.6"
}

group = "com.bcplatforms"
version = "1.0.0"
java.sourceCompatibility = JavaVersion.VERSION_21

repositories {
    mavenCentral()
}

dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("org.springframework.boot:spring-boot-starter-jdbc")
    implementation("org.postgresql:postgresql")

    // CSV processing (matching exporter2026)
    implementation("com.opencsv:opencsv:5.9")

    // Logging
    implementation("org.springframework.boot:spring-boot-starter-logging")

    // Util
    implementation("org.projectlombok:lombok")
    annotationProcessor("org.projectlombok:lombok")

    // Migrated services (versions matching their respective build files)
    implementation("com.bcp:sample-service:0.1.0-SNAPSHOT")
    implementation("com.bcplatforms:importer2026:0.0.1-SNAPSHOT")
    implementation("com.bcplatforms:exporter2026:0.0.1-SNAPSHOT")

    // Testing
    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testImplementation("org.testcontainers:testcontainers:1.21.3")
    testImplementation("org.testcontainers:postgresql:1.21.3")
    testImplementation("org.testcontainers:junit-jupiter:1.21.3")
}

tasks.withType<Test> {
    useJUnitPlatform()
}
