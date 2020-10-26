# Debugging

```
docker run --rm --name debugapi -p 3000:3000 -it ponsfrilus/debugapi
node -r ts-node/register --inspect-brk index.ts -i ~/Downloads/qdirstat.example -p http://localhost:3000
```


