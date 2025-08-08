FROM node:18-alpine

WORKDIR /app

# Install dependencies based on the preferred package manager
COPY nexcode_admin/package.json nexcode_admin/package-lock.json* ./
RUN npm ci

# Copy source code
COPY nexcode_admin/ .

# Build the application with environment variable
ARG VITE_API_BASE_URL=http://localhost:5433
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nodejs

# Set correct permissions
USER nodejs

# Expose port
EXPOSE 5433

ENV PORT 5433

# Start the application
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5433"] 