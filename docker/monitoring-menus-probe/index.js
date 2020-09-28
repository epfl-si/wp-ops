'use strict'
const fetch = require('node-fetch')
const https = require('https')
const { URL } = require('url')
const express = require('express')
const _ = require('lodash')
require('express-async-errors')
const {default: PQueue} = require('p-queue')
const prometheus = require('prom-client')  // Not actually a client
const graphlib = require('graphlib')

const app = express()
const agent = new https.Agent({
  rejectUnauthorized: false,
})

app.get('/wpprobe', async function (req, res) {
  const options = { target: req.query.target, wp_env: req.query.wp_env }
  console.log("wp_env: ", options.wp_env)
  console.log("target: ", options.target)
  const q = getQueue(options.target)
  if (q.pending) {
    // Prometheus is re-scraping the same site URL too fast.
    res.type(prometheus.contentType)
    res.send("")
  } else {
    await q.add(async () => {
      const metrics = await siteToMetrics(options)
      res.type(prometheus.contentType)
      res.send(metrics)
    })
  }
})

app.listen(8080) ///////////////////////////////////////////////////////////////

async function siteToMetrics(options) {
  const r = new prometheus.Registry()
  r.setDefaultLabels({ url: options.target, 
                       wp_env: options.wp_env })

  function menuGauge(name, help) {
    return new prometheus.Gauge({ name, help,
                                  labelNames: ['lang'],
                                  registers: [r] })
  }
  function siteGauge(name, help) {
    return new prometheus.Gauge({ name, help,
                                  registers: [r] })
  }
  function externalMenuGauge(name, help) {
    return new prometheus.Gauge({ name, help,
                                  labelNames: ['lang', 'slug', 'external_menu_uri'],
                                  registers: [r] })
  }
  function wpSite(name, help) {
    return new prometheus.Gauge({ name, help,
                                  labelNames: ['lang'],
                                  registers: [r] })
  }

  const metrics = {
    menuTime:                     menuGauge('epfl_menu_request_time_seconds',
                                            'Time in seconds it took to scrape the JSON menu'),
    menuCount:                    menuGauge('epfl_menu_count',
                                            'Number of menu entries that live on this site (not parent nor sub-sites)'),
    menuCountUnique:              menuGauge('epfl_menu_unique_count',
                                            'Number of unique menu entries that live on this site (not parent nor sub-sites)'),
    menuOrphanCount:              menuGauge('epfl_menu_orphan_count',
                                            'Number of orphan menu entries'),
    menuCycleCount:               menuGauge('epfl_menu_cycle_count',
                                            'Number of cycles in menu entries'),
    pageCount:                    siteGauge('epfl_wp_site_pages',
                                            'Number of WordPress pages on the site'),
    externalMenuSyncLastSuccess:  externalMenuGauge('epfl_externalmenu_sync_last_success',
                                                    'Last time (in UNIX epoch format) when this external menu was successfully synced'),
    externalMenuSyncFailingSince: externalMenuGauge('epfl_externalmenu_sync_failing_since',
                                                    'Time (in UNIX epoch format) at which the current streak of sync failures started'),
    epflWPSiteLangs:              wpSite('epfl_wp_site_langs',
                                         '1 for every different language configured in the site\'s Polylang plugin'),
  }

  await Promise.all([
    scrapeMenus(options, metrics),
    scrapeExternalMenus(options, metrics),
    scrapeLanguages(options, metrics),
    scrapePageCount (options, metrics)
  ])

  return r.metrics()
}

async function scrapeMenus (options, metrics) {
  for (let lang of await fetchJson(options, 'wp-json/epfl/v1/languages')) {
    await scrapeMenu(options, 'wp-json/epfl/v1/menus/top?lang=' + lang,
                     withLabels({lang}, metrics))
  }
}

async function scrapePageCount (options, metrics) {
  const pages = await fetchJson(options, 'wp-json/wp/v2/pages')
  //console.debug(pages)
  // TODO: count by languages etc. (requires some cooperation from the server, as Polylang's JSON API is not freeware)
  if (pages && typeof(pages.length) === 'number') {
    metrics.pageCount.set({}, pages.length)
  }
}


async function scrapeExternalMenus (options, metrics) {
  let externalMenus = await fetchJson(options, 'wp-json/wp/v2/epfl-external-menu')
  if ('data' in externalMenus && 'status' in externalMenus.data && externalMenus.data.status >= 400) {
    console.error(`${options.target}wp-json/wp/v2/epfl-external-menu is not accessible`)
    return;
  }
  for (externalMenu of externalMenus) {
    let labels
    if (externalMenu.meta && externalMenu.meta['epfl-emi-remote-slug']) {
      labels = { slug: externalMenu.meta['epfl-emi-remote-slug'],
                 external_menu_uri: externalMenu.meta['epfl-emi-site-url'],
                 lang: externalMenu.lang
               }
    } else {  // For compatibility, until
              // https://github.com/epfl-si/wp-plugin-epfl-menus/pull/3
              // gets pushed to production
      labels = { slug: externalMenu.slug }
    }

    const sync = externalMenu.sync_status || {},
          lastSuccess = Number(sync.last_success),
          failingSince = Number(sync.failing_since)
    if (lastSuccess)  metrics.externalMenuSyncLastSuccess.set (labels, lastSuccess)
    if (failingSince) metrics.externalMenuSyncFailingSince.set(labels, failingSince)
  }
}

async function scrapeMenu (options, path, metrics) {
  const end = startTimer()
  let menu = await fetchJson(options, path)
  metrics.menuTime.set(end())

  const items = menu.items
  metrics.menuCount.set(items.length)

  const g = new graphlib.Graph()
  for (let i of items) {
    const id = i.ID
    g.setNode(id)
  }
  metrics.menuCountUnique.set(g.nodes().length)

  let orphans = 0
  for (let i of items) {
    const id = i.ID
    const parent = i.menu_item_parent
    if (parent) {
      if (! g.hasNode(parent)) {
        orphans ++
      } else {
        g.setEdge(id, parent)
      }
    }
  }
  metrics.menuOrphanCount.set(orphans)
  metrics.menuCycleCount.set(graphlib.alg.findCycles(g).length)
}

async function scrapeLanguages (options, metrics) {
  for(let lang of await fetchJson(options, 'wp-json/epfl/v1/languages')) {
    metrics.epflWPSiteLangs.set ({
      //url: options.target,
      lang
    }, 1)
  }
}

async function fetchJson (options, path) {
  const baseUrl = new URL(options.target)
  const origHostname = baseUrl.hostname
  baseUrl.hostname = 'httpd-' + options.wp_env
  baseUrl.port = '8443'
  const apiUrl = new URL(path,
                         baseUrl.href.endsWith("/") ?
                         baseUrl.href :
                         baseUrl.href + "/")
  let results = (await fetch(apiUrl, {
    headers: { Host: origHostname },
    agent
  })).json()

  if ('data' in results && 'status' in results.data && results.data.status == 401) {
    // Avoid error in case of "coming soon" wp site
    return []
  }
  return results
}

const queues = {}
function getQueue (url) {
  if (! queues[url]) {
    queues[url] = new PQueue({concurrency: 1})
  }
  return queues[url]
}

function startTimer () {
  const now = process.hrtime.bigint()
  return () => {
    const elapsed = process.hrtime.bigint() - now
    const micro = Number(elapsed / 1000n)
    return micro / 1000000
  }
}

function withLabels (labels, metrics) {
  return _.mapValues(metrics, (metric) => {
    const setOrig = metric.set.bind(metric)
    return _.extend({
      set(val) { metric.set(labels, val) }
    }, metric)
  })
}
