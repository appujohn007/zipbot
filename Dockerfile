# Use the official Python image from the Docker Hub
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt file into the container
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of the application's code into the container
COPY . .

# Command to run the bot
CMD ["python", "main.py"]
