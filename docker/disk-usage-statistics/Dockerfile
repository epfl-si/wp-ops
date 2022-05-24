# https://nodejs.org/de/docs/guides/nodejs-docker-webapp/
FROM public.ecr.aws/bitnami/node:14

WORKDIR /usr/src/app

COPY package*.json tsconfig.json ./
RUN npm install --no-fund

COPY index.ts index.ts
CMD [ "node", "-r", "ts-node/register", "index.ts" ]
