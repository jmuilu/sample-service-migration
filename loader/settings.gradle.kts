rootProject.name = "sample-service-migration-loader"

val home = System.getProperty("user.home")

includeBuild("$home/git/importer2026")
includeBuild("$home/git/exporter2026")
includeBuild("$home/git/others/biobank-solution/sample-service")
