locals {
  env = "dev"
}

provider "google" {
  project = "${var.project}"
}

module "bigQuery" {
  source  = "../../../../infra/challenges/bigQuery"
  project = "${var.project}"
}

module "firewall" {
  source  = "../../../../infra/challenges/firewall"
  project = "${var.project}"
  network = "${var.vault_network}"
}

module "gcs" {
  source  = "../../../../infra/challenges/gcs"
  project = "${var.project}"
  bucket = "${var.bucket}"
}

module "networks" {
  source  = "../../../../infra/challenges/networks"
  project = "${var.project}"
  network = "${var.vault_network}"
}