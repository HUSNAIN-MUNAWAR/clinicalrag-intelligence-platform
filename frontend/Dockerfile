FROM node:22-alpine AS deps
WORKDIR /app
COPY frontend/package.json ./
RUN npm install
FROM node:22-alpine AS runner
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend ./
ENV NEXT_TELEMETRY_DISABLED=1
CMD ["npm", "run", "dev"]
