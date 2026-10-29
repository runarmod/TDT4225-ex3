# TDT4225-ex3

## Setup

```sh
uv sync
cp .env.example .env
docker compose up -d
```

## Running the scripts

### EDA

The EDA has been done in a jupyter notebook. Either run the notebook in VS Code, or run the following command to start a jupyter server:

```sh
uv run jupyter lab
```

### Inserting data

To insert data into the database, make sure the mongodb is running in docker, or you have configured a remote server with correct values in your `.env` file, and run the following command:

```sh
uv run insert
```

### Querying the database

To run the queries, run the following command:

```sh
uv run queries
```

## Pre-commit hooks

Install the hooks so they run before every commit:

```sh
uv run pre-commit install
```

Run the hooks over all files:

```sh
uv run pre-commit run --all-files
```
