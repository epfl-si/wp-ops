FROM docker-registry.default.svc:5000/wwp-test/wp-base
RUN mkdir /app
WORKDIR /app
COPY package.json /app
COPY package-lock.json /app
RUN npm i --no-fund
COPY *.js /app
CMD ["npm", "start"]
