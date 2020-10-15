import lines from 'lines-async-iterator'
import { AsyncIterableX, from } from 'ix/asynciterable'
import { map, flatMap } from 'ix/asynciterable/operators'
import { UnaryFunction } from 'ix/interfaces'
import fetch from 'node-fetch'
import URL from 'url'
import Debug from 'debug'
const debug = Debug("disk-usage-metrics")

function parseQdirstat(path: string) {
  return from(lines(path)).pipe(
    flatMap((x) => {
      const parsed = parseLine(x)
      return from(parsed ? [parsed] : [])
    })
  )
}

class Site {
  public label: string
  private veritasPath: string
  private static sites: Array<Site>

  static async loadAll() {
    const response = await fetch('https://wp-veritas.epfl.ch/api/v1/inventory/entries')
    const data = await response.json()
    Site.sites = data.map((wpv) => Site.fromWpVeritas(wpv))
  }

  /**
   * Find a Site by the path of one of its files or directories.
   *
   * load() must have succeeded prior.
   *
   * @returns The “best” match, i.e. the Site instance that is lowest
   *          in the filesystem tree and contains `path`.
   */
  static find(path: string): Site {
    return Site.best(Site.sites.filter((s) => s.has(path)))
  }

  static fromWpVeritas(wpVeritasRecord): Site {
    const url = new URL.URL(wpVeritasRecord.url)
    const site = new Site()
    site.label = wpVeritasRecord.ansibleHost
    site.veritasPath = `/srv/${wpVeritasRecord.openshiftEnv}/${url.hostname}/htdocs${url.pathname}`
    return site
  }

  private has(path: string) {
    return path.startsWith(this.veritasPath)
  }

  /**
   * @return The “best” (most specific i.e. lowest in the tree) site in `sites`
   */
  static best(sites: Array<Site>) {
    return sites.sort((a, b) => a.veritasPath.length - b.veritasPath.length)[0]
  }
}

type Record = {
  kind: string
  path: string
  size: number
  time: number
}

function parseLine(line: string): Record | undefined {
  const regexp = /^(.)\s+(.*?)\s+(\d+)\s+(0x[0-9a-f]+)/gm
  let matches = regexp.exec(line)
  if (matches) {
    return {
      kind: matches[1],
      path: matches[2],
      size: Number(matches[3]),
      time: Number(matches[4]),
    }
  }
}

let pathPrefix
const qualifyFiles: UnaryFunction<AsyncIterable<Record>, AsyncIterableX<Record>> = map((record) => {
  if (record.kind === 'D') {
    pathPrefix = record.path
  }
  if (record.kind === 'F' && pathPrefix) {
    record.path = `${pathPrefix}/${record.path}`
  }
  debug(record)
  return record
})

const filename = process.argv[process.argv.length - 1]
const stats: { [k: string]: { count: number } } = {}
Site.loadAll()
  .then(() =>
    parseQdirstat(filename)
      .pipe(qualifyFiles)
      .forEach((record) => {
        const site = Site.find(record.path)
        if (!site) {
          return
        }
        const label = site.label
        if (!stats[label]) {
          stats[label] = { count: 0 }
        }
        stats[label].count += 1
      })
  )
  .then(() => {
    console.log(stats)
  })
