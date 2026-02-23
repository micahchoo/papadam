FROM node:22-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:22-alpine
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
EXPOSE 1234
HEALTHCHECK --interval=30s --timeout=5s \
  CMD wget -qO- http://localhost:1234/health || exit 1
CMD ["node", "dist/index.js"]
