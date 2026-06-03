FROM node:22-alpine AS build

WORKDIR /workspace/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/index.html \
     frontend/postcss.config.js \
     frontend/tailwind.config.js \
     frontend/tsconfig.app.json \
     frontend/tsconfig.json \
     frontend/tsconfig.node.json \
     frontend/vite.config.ts ./
COPY frontend/public public
COPY frontend/src src

RUN npm run build

FROM nginx:1.27-alpine

COPY deploy/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /workspace/frontend/dist /usr/share/nginx/html

EXPOSE 80
