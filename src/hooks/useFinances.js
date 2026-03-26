import { useState, useEffect } from 'react'

let cachedData = null
let fetchPromise = null

export function useFinances() {
  const [data, setData] = useState(cachedData)
  const [loading, setLoading] = useState(!cachedData)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (cachedData) return
    if (!fetchPromise) {
      fetchPromise = fetch('./data.json').then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
    }
    fetchPromise
      .then(d => {
        cachedData = d
        setData(d)
        setLoading(false)
      })
      .catch(e => {
        setError(e)
        setLoading(false)
      })
  }, [])

  return { data, loading, error }
}

/** Sum of transaction amounts for a given category name string. */
export function totalAmount(transactions, category) {
  return transactions
    .filter(t => t.category === category)
    .reduce((sum, t) => sum + t.amount, 0)
}

/** Sum of all transaction amounts. */
export function balance(transactions) {
  return transactions.reduce((sum, t) => sum + t.amount, 0)
}

/** Flatten all transactions from a year object. */
export function allTransactions(year) {
  return year.months.flatMap(m => m.transactions)
}
