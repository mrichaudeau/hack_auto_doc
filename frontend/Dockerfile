FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy dependency files first for better layer caching
COPY package.json package-lock.json ./

# Install dependencies using clean install for reproducibility
RUN npm ci

# Copy application code
COPY . .

# Expose Vite dev server port
EXPOSE 3000

# Configure Vite for Docker environment
ENV HOST=0.0.0.0 \
    PORT=3000 \
    CHOKIDAR_USEPOLLING=true

# Run Vite development server with hot reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
