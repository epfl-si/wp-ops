# https://nodejs.org/de/docs/guides/nodejs-docker-webapp/
FROM node:13

WORKDIR /usr/src/app

COPY package*.json ./
RUN npm install

COPY index.js index.js
EXPOSE 8080
CMD [ "node", "index.js" ]
