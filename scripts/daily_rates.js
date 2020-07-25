const https = require('https')
const fs = require('fs')

async function performRequest(options) {
  return new Promise((resolve, reject) => {
    const chunks = []

    const req = https.request(options, res => {
        res.on('data', d => {
          chunks.push(d)
        })

        res.on('error', e => reject(e))

        res.on('end', () => resolve(chunks.join('')))
      })
    req.on('error', e => reject(e))
    req.write(options.body || '')
    req.end()
  })
}

function getDateString(date) {
  return `${date.getFullYear()}-${date.getMonth()+1}-${date.getDate()}`
}

async function getRates(date) {
  return await performRequest({
    hostname: 'api.ratesapi.io',
    path: `/api/${getDateString(date)}?base=USD`,
    method: 'GET',
    agent: false,
    headers: {
      'Content-Type': 'application/json'
    },
    maxRedirects: 20
  })
    .then(res => JSON.parse(res))
}

function nDaysAgo(n) {
  let d = new Date();
  d.setDate(d.getDate() - n);
  return d;
}

function range(n) {
  return (new Array(n)).fill(0).map((x, i) => i)
}

async function getRatesData() {
  return await Promise.all(
    range(1095).reverse().map(i => nDaysAgo(i)).map(d => getRates(d))
  )
}

async function main() {
  const data = await getRatesData()
  return fs.writeFileSync('data.json', JSON.stringify(data))
}

main()

// getRates(new Date()).then(console.log)