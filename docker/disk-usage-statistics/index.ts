import * as fs from 'fs'

const parseQdirstat  = async function (file) {
  const read = fs.createReadStream(file, {encoding: 'utf8'})
}
