# Use an official Python runtime as a parent image
FROM python:3.13-bullseye

# Install the project into `/app`
WORKDIR /app

# Copy requirements files
COPY requirements.txt .

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

ADD . /app

# Expose the desired port
EXPOSE 3000

# Run the application
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "3000"]