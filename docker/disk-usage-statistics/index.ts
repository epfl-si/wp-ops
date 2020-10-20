import Debug from 'debug'
const debug = Debug('disk-usage-metrics')
import http from 'http'
import URL from 'url'
import fetch from 'node-fetch'
import lines from 'lines-async-iterator'
import { UnaryFunction } from 'ix/interfaces'
import { AsyncIterableX, from } from 'ix/asynciterable'
import { map, flatMap } from 'ix/asynciterable/operators'

// -- Args ---------------------------------------------------------------------
const lecommander = require('commander')
lecommander.version(require('./package.json').version)
lecommander
  .name('npm start -- ')
  .usage('-d -i qdirstat -p http://localhost:9091')
  .description('An application that parse qdirstat output file and send metrics to a prometheus pushgateway.')
  .option('-d, --debug', 'output extra debugging')
  .option('-i, --input-file <file>', '`qdirstat` input file')
  .option('-p, --pushgateway-base-url <url>', 'prometheus pushgateway url')
  .option('-w, --webhook', 'if true, wait for webhook')

lecommander.parse(process.argv)

if (lecommander.debug) console.log(lecommander.opts())
console.log('Run details:')
if (lecommander.inputFile) console.log(` - input-file: ${lecommander.inputFile}`)
if (!lecommander.pushgatewayBaseUrl) {
  lecommander.pushgatewayBaseUrl = 'http://pushgateway:9091/'
}
console.log(` - pushgateway-base-url: ${lecommander.pushgatewayBaseUrl}`)
// -- End Args -----------------------------------------------------------------

function parseQdirstat(path: string) {
  return from(lines(path)).pipe(
    flatMap((x) => {
      const parsed = parseLine(x)
      return from(parsed ? [parsed] : [])
    })
  )
}

class Site {
  private veritasPath: string
  private static sites: Array<Site>
  private static bestCache: { [path: string]: Site } = {}
  public label: string
  public url: string

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
  static find(pathPrefix: string): Site {
    if (!pathPrefix) return
    if (!(pathPrefix in Site.bestCache)) {
      Site.bestCache[pathPrefix] = Site.best(Site.sites.filter((s) => s.has(pathPrefix)))
    }
    const retval = Site.bestCache[pathPrefix]
    debug(`find(${pathPrefix}) -> ${retval ? retval.label : '<undefined>'}`)
    return retval
  }

  static fromWpVeritas(wpVeritasRecord: any): Site {
    const url = new URL.URL(wpVeritasRecord.url)
    const site = new Site()
    site.label = wpVeritasRecord.ansibleHost
    site.veritasPath = `/srv/${wpVeritasRecord.openshiftEnv}/${url.hostname}/htdocs${url.pathname}`
    site.url = wpVeritasRecord.url
    return site
  }

  private has(path: string) {
    return path.startsWith(this.veritasPath)
  }

  /**
   * @return The “best” (most specific i.e. lowest in the tree) site in `sites`
   */
  static best(sites: Array<Site>) {
    return sites.sort((a, b) => b.veritasPath.length - a.veritasPath.length)[0]
  }
}

type Record = {
  kind: string
  path?: string
  dir?: string
  size: number
  time: number
}

function parseLine(line: string): Record | undefined {
  const regexp = /^(.)\s+(.*?)\s+(\d+)\s+(0x[0-9a-f]+)/gm
  let matches = regexp.exec(line)
  if (matches) {
    const kind = matches[1],
      size = Number(matches[3]),
      time = Number(matches[4])
    if (kind === 'D') {
      return {
        kind,
        size,
        time,
        dir: matches[2],
      }
    } else {
      return {
        kind,
        size,
        time,
        path: matches[2],
      }
    }
  }
}

let pathPrefix: string
const qualifyFiles: UnaryFunction<AsyncIterable<Record>, AsyncIterableX<Record>> = map((record) => {
  if (record.kind === 'D') {
    pathPrefix = record.path
  }
  if (record.kind === 'F') {
    record.dir = pathPrefix
  }
  debug(record)
  return record
})

type SiteStats = {
  files: {
    total: number
    'wp-content': number
    uploads: number
  }
  size: {
    total: number
    'wp-content': number
    uploads: number
  }
  url: string
}

async function main() {
  const stats: { [k: string]: SiteStats } = {}
  await Site.loadAll()

  await parseQdirstat(lecommander.inputFile)
    .pipe(qualifyFiles)
    .forEach((record) => {
      const site = Site.find(record.dir)
      if (!site) {
        return
      }
      const label = site.label
      if (!stats[label]) {
        stats[label] = {
          files: { total: 0, 'wp-content': 0, uploads: 0 },
          size: { total: 0, 'wp-content': 0, uploads: 0 },
          url: site.url,
        }
      }
      stats[label].files.total += 1
      stats[label].size.total += record.size

      if (record.dir.includes('/wp-content/')) {
        stats[label].files['wp-content'] += 1
        stats[label].size['wp-content'] += record.size
      }

      if (record.dir.includes('/wp-content/uploads/')) {
        stats[label].files.uploads += 1
        stats[label].size.uploads += record.size
      }
    })

  console.log(stats)

  for (const [ansibleHost, site] of Object.entries(stats)) {
    let result = ''
    for (const [data, diskUsage] of Object.entries(site)) {
      if (data === 'url') {
        continue
      }
      for (const [key, value] of Object.entries(diskUsage)) {
        let metric = `wp_disk_usage_${data}_${keyify(key)}`

        // Add metrics' type and help only once
        let help = data === 'files' ? `Files count of ${key}.` : data === 'size' ? `Total size of ${key} in bytes.` : ''
        result += `# TYPE ${metric} gauge\n`
        result += `# HELP ${metric} ${help}\n`
        result += `${metric}{url="${site.url}"} ${value}\n`
      }
    }

    let pushgatewayUrl = `${lecommander.pushgatewayBaseUrl}/metrics/job/wp_disk_usage/instance/${ansibleHost}`
    await fetch(pushgatewayUrl, {
      method: 'POST',
      body: result,
      headers: { 'Content-Type': 'application/text' },
    })
    console.log(result)
  }
}

function keyify(label: string): string {
  return label.replace(/-/g, '_')
}

class Webhook {
  private server
  private response

  public async await(port?: number) {
    if (!port) port = 8080
    return new Promise((resolve) => {
      this.server = http
        .createServer((req, res) => {
          this.response = res
          resolve()
        })
        .listen(port)
    })
  }

  public async success() {
    // https://nodejs.org/api/http.html
    this.response.statusCode = 204
    this.response.statusMessage = "It's cool dude"
    this.response.end()
    this.server.close()
  }
}

if (lecommander.webhook) {
  const w = new Webhook()
  w.await()
    .then(main)
    .then(() => w.success())
} else {
  main()
}
