FROM node:20-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
# Default nginx configuration port 80
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
