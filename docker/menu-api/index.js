const express = require('express')
const app = express()
const port = 3000

const MENU_JSON = require('./epfl-full-top-fr-menu.json')


const searchEntryByID = (id) => {
  const parent = MENU_JSON.find(o => o.ID === id)
  return parent
}

const searchEntryByURL = (entry) => {
  const site = MENU_JSON.find(o => o.epfl_soa === entry)

  if (site) {
    return {
      title: site.title,
      url: site.url,
      menu_item_parent: site.menu_item_parent,
    }
  }
}

const searchAllParentsEntriesByID = (entry) => {
  const parentEntry = searchEntryByID(entry.menu_item_parent)

  if (parentEntry &&
    parentEntry.menu_item_parent &&
    parentEntry.menu_item_parent !== '0') {
    const parents = searchAllParentsEntriesByID(parentEntry)
    return [...parents, parentEntry];
  } else {
    return [parentEntry];
  }
}

app.get('/', (req, res) => {
  res.send('Hello World!')
})

app.get('/breadcrumb', (req, res) => {
  const url = req.query.url,
        lang = req.query.lang;

  const firstSite = url ? searchEntryByURL(url) : undefined

  const breadcrumbForURL = firstSite !== undefined ? [
    ...searchAllParentsEntriesByID(firstSite),
    firstSite,
    ] : []

  res.json({
    status: "OK",
    breadcrumb: breadcrumbForURL
  })
})

app.listen(port, () => {
  console.log(`menu-api listening on port ${port}`)
})
