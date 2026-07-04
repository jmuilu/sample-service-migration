# Antigravity (AGY) - Project Rules for sample-service-migration

Tämä tiedosto sisältää projektikohtaiset tekoälysäännöt ja parhaat käytännöt `sample-service-migration` -työtilaan. Säännöt latautuvat automaattisesti kaikille tekoälyistunnoille.

---

## 1. Migration Architecture: Generic ETL (Zero-Compile)
*   **Ei Java-lataajia:** Älä kirjoita uutta custom Java-latauskoodia `loader/src/...` hakemistoon. Kaikki uudet taulumigraatiot suoritetaan geneerisen `importer2026`-työkalun, YAML-manifestien ja JavaScript-transformaatioiden avulla.
*   **Työtilan tiedostot:** Kaikki uudet manifestit tallennetaan kansioon `config/manifests/` ja transformaatiot kansioon `config/scripts/`.
*   **Muutoksista ilmoittaminen (Notification on major changes):** Jos huomaat tarpeen tehdä suurempia koodimuutoksia tai arkkitehtonisesti merkittäviä laajennuksia geneerisiin `importer2026`- tai `exporter2026`-työkaluihin, **ilmoita tästä aina etukäteen käyttäjälle** ja odota vahvistusta ennen muutosten tekemistä.

## 2. Status of Migrations
* `sample_type`, `container_type`, `container` ja `sample` migraatiot ovat **VALMIIT** ja testattu.
* Kaikki neljä ydintaulua on nyt migroitu. Seuraa tarkasti [LLM_MIGRATION_RUNBOOK.md](file:///Users/muilu/git/others/sample-service-migration/LLM_MIGRATION_RUNBOOK.md) -tiedoston ohjeita mahdollisissa jatkoaskelissa.

## 3. Tool Execution Details
*   **Postgres-ajuri:** Kun suoritat `importer2026` gradle-ajona tai JAR-tiedostona PostgreSQL-kantaan, lisää aina mukaan Postgres-ajurin pakotus:
    `--spring.datasource.driver-class-name=org.postgresql.Driver`
*   **Polut:** Koska Gradle siirtää työhakemiston suoritettavan projektin alikansioon, käytä aina absoluuttisia tiedostopolkuja argumenteissa `--csv` ja `--manifest`.
*   **Sekvenssien nollaus:** Aina kun taulu on siirretty, resetoi sen PostgreSQL-sekvenssi välittömästi.
*   **Self-join lajittelu:** Jos taulussa on itsereferenssejä (kuten `sample` ja `container`), käytä aina `--sort-self-joins` vipua ladatessasi, jotta parent-ID:t ratkeavat dynaamisesti oikeassa järjestyksessä.

---

## 4. Referenssit
*   Aktiivinen Runbook: [LLM_MIGRATION_RUNBOOK.md](file:///Users/muilu/git/others/sample-service-migration/LLM_MIGRATION_RUNBOOK.md)
*   Skeemamäppäykset: [schema-mapping.md](file:///Users/muilu/git/others/sample-service-migration/docs/schema-mapping.md)
