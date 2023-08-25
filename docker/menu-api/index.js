const express = require('express')
const app = express()
const port = 3000

app.get('/', (req, res) => {
  res.send('Hello World!')
})

app.get('/breadcrumb', (req, res) => {
  const blogname = req.query.blogname,
        lang = req.query.lang;
  res.json({ status: "OK", breadcrumb:
             [{url: "https://example.com", title: "Toto"},
              {url: "https://example.com", title: "Tutu"}] })
})


app.listen(port, () => {
  console.log(`Example app listening on port ${port}`)
})
