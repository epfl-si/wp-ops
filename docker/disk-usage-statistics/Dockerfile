# https://nodejs.org/de/docs/guides/nodejs-docker-webapp/
FROM node:13

WORKDIR /usr/src/app

COPY package*.json ./
RUN npm install

COPY index.ts index.ts
CMD [ "node", "-r", "ts-node/register", "index.ts" ]
