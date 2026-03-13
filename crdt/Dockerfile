FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force
COPY --from=build /app/dist ./dist

USER node

EXPOSE 1234
HEALTHCHECK --interval=30s --timeout=5s \
  CMD wget -qO- http://localhost:1234/health || exit 1
CMD ["node", "dist/index.js"]
