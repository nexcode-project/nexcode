FROM node:18-alpine

WORKDIR /app

# Install dependencies based on the preferred package manager
COPY nexcode_web/package.json nexcode_web/package-lock.json* ./
RUN npm ci --only=production

# Copy source code
COPY nexcode_web/ .

# Build the application
RUN npm run build

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Set correct permissions
USER nextjs

# Expose port
EXPOSE 3000

ENV PORT 3000

# Start the application
CMD ["npm", "start"] 