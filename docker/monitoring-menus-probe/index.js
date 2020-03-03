'use strict'
const fetch = require("node-fetch")
const express = require('express')
const _ = require('lodash')
require('express-async-errors')
const {default: PQueue} = require('p-queue')
const prometheus = require('prom-client')  // Not actually a client
const graphlib = require("graphlib")

const app = express()

app.get('/wpmenuprobe', async function (req, res) {
  const target = req.query.target
  const q = getQueue(target)
  if (q.pending) {
    // Prometheus is re-scraping the same site URL too fast.
    res.type(prometheus.contentType)
    res.send("")
  } else {
    await q.add(async () => {
      const metrics = await siteToMetrics(target)
      res.type(prometheus.contentType)
      res.send(metrics)
    })
  }
})

app.listen(8080) ///////////////////////////////////////////////////////////////

async function siteToMetrics(siteUrl) {
  const r = new prometheus.Registry()
  r.setDefaultLabels({url: siteUrl})
  function gauge(name, help) {
    return new prometheus.Gauge({ name, help, labelNames: ['lang'], registers: [r] })
  }
  const metrics = {
    menuTime: gauge('epfl_menu_request_time_seconds',
                    'Time in seconds it took to scrape the JSON menu'),
    menuCount: gauge('epfl_menu_count',
                     'Number of menu entries that live on this site (not parent nor sub-sites)'),
    menuCountUnique: gauge('epfl_menu_unique_count',
                     'Number of unique menu entries that live on this site (not parent nor sub-sites)'),
    menuOrphanCount: gauge('epfl_menu_orphan_count',
                     'Number of orphan menu entries'),
    menuCycleCount: gauge('epfl_menu_cycle_count',
                     'Number of cycles in menu entries'),
  }

  await scrapeMenus(siteUrl, metrics)

  return r.metrics()
}

async function scrapeMenus (siteUrl, metrics) {
  for(let lang of await fetchJson(siteUrl + '/wp-json/epfl/v1/languages')) {
    await scrapeMenu(siteUrl + '/wp-json/epfl/v1/menus/top?lang=' + lang,
                     withLabels({lang}, metrics))
  }
}

async function scrapeMenu (menuUrl, metrics) {
  const end = startTimer()
  let menu = await fetchJson(menuUrl)
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

async function fetchJson (url) {
  return fetch(url).then((resp) => resp.json())
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
