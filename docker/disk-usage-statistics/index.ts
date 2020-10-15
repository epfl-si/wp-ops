import lines from "lines-async-iterator"
import { from } from 'ix/asynciterable'

import { flatMap } from 'ix/asynciterable/operators'

function parseQdirstat (path: string) {
  return from(lines(path))
    .pipe(flatMap((x) => {
      const parsed = parseLine(x)
      return from(parsed ? [parsed] : [])
    }))
}

type Record = {
  kind: string
  path: string
  size: number
  time: number
}

function parseLine (line : string) : Record|undefined {
  const regexp = /^(.)\s+(.*?)\s+(\d+)\s+(0x[0-9a-f]+)/gm
  let matches = regexp.exec(line)
  if (matches) {
    return { kind: 'F', path: 'path', size: 0, time: 0}
  }
}

const filename = process.argv[process.argv.length - 1]
parseQdirstat(filename).forEach(console.log)
