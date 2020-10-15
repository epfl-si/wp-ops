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

parseQdirstat(process.argv[process.argv.length - 1]).subscribe((line) => console.log(line))
