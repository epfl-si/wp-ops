const express = require('express')
const app = express()
const port = 3000

const MENU_JSON = require('./new-menu.json')
//console.log(MENU_JSON)

const searchEntryByURL = (entry) => {
  // console.debug("searchEntryByURL", entry)
  let site = MENU_JSON.find(o => o.epfl_soa === entry);
  // console.log(site)
  return site
}
const searchEntryByID = (id) => {
  // console.debug("searchEntryByID", id)
  let parent = MENU_JSON.find(o => o.ID === id);
  // console.log(parent)
  return parent
}
let currentSite = searchEntryByURL('https://www.epfl.ch/research/awards/')
let parrent = searchEntryByID(currentSite.menu_item_parent)

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
  console.log(`menu-api listening on port ${port}`)
})
