# Use an official Python runtime as a parent image
FROM python:3.10.0

# Set the working directory in the docker image
WORKDIR /usr/app/src

# Copy the content of the local src directory to the working directory
COPY . ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

# Run your Python script when the container launches
CMD ["python", "./engine-scraper.py"]
