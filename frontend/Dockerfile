FROM node:22-alpine AS build
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:22-alpine AS dev
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 8080
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

FROM nginx:alpine AS prod
COPY --from=build /app/dist /usr/share/nginx/html
RUN printf 'server {\n    listen 0.0.0.0:8080;\n    root /usr/share/nginx/html;\n    location / {\n        try_files $uri $uri/ /index.html;\n    }\n}\n' > /etc/nginx/conf.d/default.conf && sed -i 's#/var/run/nginx.pid#/tmp/nginx.pid#;s#/run/nginx.pid#/tmp/nginx.pid#' /etc/nginx/nginx.conf && chown -R nginx:nginx /var/cache/nginx /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1:8080/
USER nginx
CMD ["nginx", "-g", "daemon off;"]
