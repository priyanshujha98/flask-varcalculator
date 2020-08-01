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
  // const month = `0${date.getMonth() + 1}`.slice(-2)
  // const d = `0${date.getDate()}`.slice(-2)
  const month = date.getMonth() + 1
  const d = date.getMonth() + 1
  
  return `${date.getFullYear()}-${month}-${d}`
}

async function getRates(date) {
  try {
    return await performRequest({
      hostname: 'api.ratesapi.io',
      path: `/api/${getDateString(date)}?base=USD`,
      method: 'GET',
      agent: false,
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: 3000,
      rejectUnauthorized: false,
      maxRedirects: 20
    })
      .then(res => JSON.parse(res))
  } catch(e) {
    console.error(e)
  }
}

// async function getRawRates(date) {
//   return await performRequest({
//     hostname: 'v2.api.forex',
//     path: `/historics/${getDateString(date)}.json?from=USD&key=demo`,
//     method: 'GET',
//     maxRedirects: 20,
//   })
// }

// async function getRates(date) {
//   try {
//     const data = await getRawRates(date)
//     const parsedRates = {};
//     Object.keys(data['rates_histo'])
//       .forEach(k => {
//         parsedRates[k] = data['rates_histo'][k]['close']
//       })

//     return {
//       rates: parsedRates
//     }
//   } catch(e) {
//     console.error('error', e)
//   }
  
//   return { rates: {} }
// }

function nDaysAgo(n) {
  let d = new Date();
  d.setDate(d.getDate() - n);
  return d;
}

function range(n) {
  return (new Array(n+1)).fill(0).map((x, i) => i).filter(x => x)
}

async function getRatesData() {
  return await Promise.all(
    range(2190).reverse().map(i => nDaysAgo(i)).map(d => getRates(d))
  )
}

async function main() {
  try {
    const data = await getRatesData()
    return fs.writeFileSync('data.json', JSON.stringify(data))
  } catch(e) {
    console.log('error', e)
  }
  return
}

main()

// getRates(nDaysAgo(100)).then(console.log)