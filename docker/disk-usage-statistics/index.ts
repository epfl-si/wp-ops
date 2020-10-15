import lines from "lines-async-iterator";
import { AsyncIterableX, from } from "ix/asynciterable";
import { map, flatMap } from "ix/asynciterable/operators";
import { UnaryFunction } from "ix/interfaces";

function parseQdirstat (path: string) {
  return from(lines(path)).pipe(
    flatMap((x) => {
      const parsed = parseLine(x);
      return from(parsed ? [parsed] : []);
    })
  )
}

class Site {

  public label : string

  static async load () {
    
  }

  /**
   * Find a Site by the path of one of its files or directories.
   * 
   * load() must have succeeded prior.
   *  
   * @returns The “best” match, i.e. the Site instance that is lowest
   *          in the filesystem tree and contains `path`.
   */
  static find (path: String): Site {
    
    const s = new Site
    s.label = "mu"
    return s
  }
}

type Record = {
  kind: string;
  path: string;
  size: number;
  time: number;
};

function parseLine (line: string): Record | undefined {
  const regexp = /^(.)\s+(.*?)\s+(\d+)\s+(0x[0-9a-f]+)/gm;
  let matches = regexp.exec(line);
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
const qualifyFiles : UnaryFunction<AsyncIterable<Record>, AsyncIterableX<Record>> = map((record) => {
  if (record.kind === 'D') {
    pathPrefix = record.path
  }
  if (record.kind === 'F' && pathPrefix) {
    record.path = `${pathPrefix}/${record.path}`
  }
  return record
})

const filename = process.argv[process.argv.length - 1]
const stats : {[k: string] : {count: number}} = {}
parseQdirstat(filename).pipe(qualifyFiles).forEach((record) => {
  if (! stats[Site.find(record.path).label]){
    stats[Site.find(record.path).label] = {count: 0}
  } 
  stats[Site.find(record.path).label].count += 1;
}).then(() => {
  console.log(stats)
})
