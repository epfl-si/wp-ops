const express = require('express')
const app = express()
const port = 3000

const MENU_JSON_FR = require('/srv/menus/epfl-full-top-fr-menu.json')
const MENU_JSON_EN = require('/srv/menus/epfl-full-top-en-menu.json')
const MENU_JSON_DE = require('/srv/menus/epfl-full-top-de-menu.json')


const searchEntryByID = (id, menuData) => {
  const parent = menuData.find(o => o.ID === id)
  return parent
}

const searchEntryByURL = (entry, menuData) => {
  const site = menuData.find(o => o.epfl_soa === entry)

  if (site) {
    return {
      title: site.title,
      url: site.url,
      menu_item_parent: site.menu_item_parent,
    }
  }
}

const searchAllParentsEntriesByID = (entry, menuData) => {
  const parentEntry = searchEntryByID(entry.menu_item_parent, menuData)

  if (parentEntry &&
    parentEntry.menu_item_parent &&
    parentEntry.menu_item_parent !== '0') {
    const parents = searchAllParentsEntriesByID(parentEntry, menuData)
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

  const menuData = lang == 'de' ? MENU_JSON_DE : 
                   lang == 'fr' ? MENU_JSON_FR : 
                                  MENU_JSON_EN

  const firstSite = url ? searchEntryByURL(url, menuData) : undefined

  const breadcrumbForURL = firstSite !== undefined ? [
    ...searchAllParentsEntriesByID(firstSite, menuData),
    ] : []

  res.json({
    status: "OK",
    breadcrumb: breadcrumbForURL
  })
})

app.listen(port, () => {
  console.log(`menu-api listening on port ${port}`)
})
