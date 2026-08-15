# ---- Base ----
FROM node:22-alpine AS base
WORKDIR /app
COPY package*.json ./

# ---- Sviluppo ----
FROM base AS development
RUN npm ci
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]

# ---- Build (per produzione) ----
FROM base AS build
RUN npm ci
COPY . .
RUN npm run build

# ---- Produzione ----
FROM nginx:alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
