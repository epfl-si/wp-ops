# https://nodejs.org/de/docs/guides/nodejs-docker-webapp/
FROM public.ecr.aws/bitnami/node:13

WORKDIR /usr/src/app

COPY package*.json ./
RUN npm install --no-fund

COPY index.js index.js
EXPOSE 8080
CMD [ "node", "index.js" ]
