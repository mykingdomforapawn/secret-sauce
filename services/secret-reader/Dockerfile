# Uses a minimal, official Python image to keep the build size small.
FROM python:3.9-slim

# Sets the working directory inside the container.
WORKDIR /app

# Copies the dependency file first to leverage Docker's layer caching.
COPY requirements.txt .

# Installs the Python dependencies listed in the requirements file.
RUN pip install --no-cache-dir -r requirements.txt

# Copies the main application source code into the container.
COPY main.py .

# Documents that the container listens on port 5000.
EXPOSE 5000

# Defines the default command to start the application.
CMD ["python", "main.py"]
