terraform {
  backend "gcs" {
    bucket = "aix-data-stocks-dev-tfstate"
    prefix = "env/dev"
  }
}