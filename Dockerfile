# Alpine Linux Latest Image
FROM alpine:latest

# Install Linux packages required for Arris modem monitoring app
RUN apk add --no-cache python3 python3-dev

# Where the application lives
WORKDIR /opt/arrismonitor

# Python virtual environment
ENV VIRTUAL_ENV=/opt/arrismonitor/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy Directory into directory
COPY main.py /opt/arrismonitor/main.py

# Run the application
CMD ["python3", "main.py"]
