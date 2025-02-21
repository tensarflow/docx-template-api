# DOCX Template API

This project is a FastAPI application that provides an API for managing and generating DOCX templates. It includes endpoints for uploading, listing, and deleting templates, as well as generating documents from templates.

## Features

- Upload DOCX templates
- List available templates
- Delete templates
- Generate documents from templates and convert them to PDF

## Requirements

- Docker
- Docker Compose

## Getting Started

### Clone the Repository

```bash
git clone https://github.com/yourusername/docx-template-api.git
cd docx-template-api
```

### Build and Run the Application

1. **Build the Docker Image**

   Use the following command to build the Docker image:

   ```bash
   docker-compose build
   ```

2. **Run the Application**

   Start the application using Docker Compose:

   ```bash
   docker-compose up
   ```

   This will start the FastAPI application on `http://localhost:8000`.

### Access the API

Once the application is running, you can access the API documentation at `http://localhost:8000/docs`.

### API Endpoints

- **GET /**: Returns a welcome message.
- **POST /upload-template/**: Upload a DOCX template.
- **GET /templates/**: List all available templates.
- **DELETE /delete-template/{template_id}**: Delete a specific template.
- **POST /generate-document/**: Generate a document from a template and convert it to PDF.

## Project Structure

- `app/main.py`: The main application file.
- `app/routers/`: Contains the API routers for templates and document generation.
- `app/models.py`: Defines the database models.
- `app/database.py`: Database configuration and initialization.
- `Dockerfile`: Docker configuration for building the application image.
- `docker-compose.yml`: Docker Compose configuration for running the application.

## Volumes

The application uses Docker volumes to persist data:

- `templates`: Stores uploaded DOCX templates.
- `generated_docs`: Stores generated documents.

## Environment Variables

You can configure the application using environment variables. Update the `docker-compose.yml` file to set any necessary environment variables.
