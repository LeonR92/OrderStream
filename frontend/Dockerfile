# Use an official lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install UV (Ultra-Fast Package Manager)
RUN pip install uv

# Copy `pyproject.toml` for dependencies
COPY pyproject.toml .
RUN uv pip install --no-cache-dir .

# Copy the application files
COPY . .

# Expose Flask port
EXPOSE 5001

# Run the Flask app with Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "app:app"]
