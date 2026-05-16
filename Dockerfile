FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    # Node.js (JavaScript + TypeScript)
    nodejs npm \
    # Java
    default-jdk \
    # C++
    g++ \
    # C# (.NET SDK)
    wget apt-transport-https \
    && rm -rf /var/lib/apt/lists/*

# Install .NET SDK 8.0
RUN wget -q https://dot.net/v1/dotnet-install.sh -O /tmp/dotnet-install.sh \
    && chmod +x /tmp/dotnet-install.sh \
    && /tmp/dotnet-install.sh --channel 8.0 --install-dir /usr/share/dotnet \
    && ln -s /usr/share/dotnet/dotnet /usr/bin/dotnet \
    && rm /tmp/dotnet-install.sh

# Install TypeScript 5.x globally (TS 6+ deprecates --moduleResolution node)
RUN npm install -g typescript@5

WORKDIR /devbench
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Verify all runtimes are available
RUN python --version \
    && node --version \
    && javac -version \
    && g++ --version | head -1 \
    && dotnet --version \
    && tsc --version

CMD ["python", "evaluation/compute_pass_at_1.py"]
