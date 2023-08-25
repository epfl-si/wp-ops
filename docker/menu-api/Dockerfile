FROM docker-registry.default.svc:5000/wwp-test/wp-base
RUN mkdir /app
COPY package.json /app
COPY package-lock.json /app
RUN npm i --no-fund
COPY . /app
WORKDIR /app
CMD ["node", "index.js"]
