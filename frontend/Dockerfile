FROM node:20 AS build-stage

WORKDIR /app

COPY package*.json .
RUN npm install

COPY . .

RUN npm run build

FROM nginx:stable AS production-stage

COPY --from=build-stage /app/dist /etc/nginx/html
COPY ./nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
