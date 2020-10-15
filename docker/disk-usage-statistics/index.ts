import Rx from 'rx'
import LineByLineReader from 'line-by-line'

function parseQdirstat (path: string) : Rx.Observable<string> {
  const rl = new LineByLineReader(path)

  return Rx.Observable.fromEvent<string>(rl, 'line')
    .takeUntil(Rx.Observable.fromEvent(rl, 'close'))
}

type Record = {
  kind: string
  path: string
  size: number
  time: number
}

function parseLine (line) {
  const regexp = /^(.)\s+(.*?)\s+(\d+)\s+(0x[0-9a-f]+)/gm;
  let matches = regexp.exec(line)
  // console.log(matches)
  return { kind: 'F', path: 'path', size: 0, time: 0}
}

parseQdirstat(process.argv[process.argv.length - 1]).subscribe(
  (line) => {
    // console.log(line)
    let parsedLine = parseLine(line)
    console.log(parsedLine)
  }
)
