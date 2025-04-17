# Stage 1: Builder stage – install dependencies, build, then prune dev deps
FROM node:18-buster-slim AS builder
WORKDIR /app
ENV PATH=/usr/local/bin:$PATH

# Install global build tools so that tsc and shx are available
RUN npm install -g typescript shx

# Copy package files and remove the prepare script to prevent automatic build
COPY package*.json ./
# Remove the "prepare" script from package.json using sed (Debian has sed)
RUN sed -i '/"prepare":/d' package.json

# Install dependencies (using npm ci for a clean install)
RUN npm ci

# Copy the rest of the source code
COPY . .

# Run the build manually (this uses our global tsc and shx)
RUN npm run build

# Remove dev dependencies, leaving only production dependencies.
RUN npm prune --production

# Stage 2: Production stage – copy built artifacts and production node_modules
FROM node:18-buster-slim
WORKDIR /app

# Copy the entire built app from the builder stage
COPY --from=builder /app .

# Expose the port used by mcp-stagehand (adjust if needed)
EXPOSE 3002

# Start the MCP server from the built output
CMD ["node", "dist/index.js"]
