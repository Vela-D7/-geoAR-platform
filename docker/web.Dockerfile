# GeoAR operator console (Next.js). Build context = repo root.
FROM node:22-alpine AS build
WORKDIR /app
COPY web-app/package.json web-app/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web-app .
RUN npm run build

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/package.json /app/package-lock.json ./
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/.next ./.next
COPY --from=build /app/next.config.js ./
USER node
EXPOSE 3000
CMD ["npx", "next", "start", "-p", "3000"]
