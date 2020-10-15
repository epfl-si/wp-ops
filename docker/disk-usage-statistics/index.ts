import * as fs from 'fs/promises'
import { createReadStream } from 'fs'
import Rx from 'rx'

import { readline } from 'readline');


async function parseQdirstat (path: string) {  
  const read = createReadStream(path, {encoding: 'utf8'})

  read.on('data',
    function (data) {
      console.log(data)
      if (data.startsWith("#")) {

      }
    }
  )
}

type Record = {
  kind: string
  path: string
  size: number
  time: number
}

parseQdirstat(process.argv[process.argv.length - 1])
