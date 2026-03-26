import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Table, TableBody, TableCell, TableContainer, TableFooter,
  TableHead, TableRow, TableSortLabel, Paper,
} from '@mui/material'
import { totalAmount, balance } from '../hooks/useFinances'
import { fmt } from '../utils/format'

const MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

export default function CategoryTable({ year, categories }) {
  const [sort, setSort] = useState({ key: 'category', dir: 'asc' })

  function handleSort(key) {
    setSort(s => s.key === key
      ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' }
      : { key, dir: 'asc' }
    )
  }

  function monthTotal(monthIndex, category) {
    const month = year.months.find(m => m.index === monthIndex)
    return month ? totalAmount(month.transactions, category) : 0
  }

  function yearTotal(category) {
    return year.months.reduce((sum, m) => sum + totalAmount(m.transactions, category), 0)
  }

  function yearAverage(category) {
    return year.months.length === 0 ? 0 : yearTotal(category) / year.months.length
  }

  const sortedCategories = [...categories].sort((a, b) => {
    const dir = sort.dir === 'asc' ? 1 : -1
    if (sort.key === 'category') return dir * a.localeCompare(b)
    if (sort.key === 'total') return dir * (yearTotal(a) - yearTotal(b))
    if (sort.key === 'average') return dir * (yearAverage(a) - yearAverage(b))
    const mi = parseInt(sort.key)
    return dir * (monthTotal(mi, a) - monthTotal(mi, b))
  })

  const yearBalance = year.months.reduce((sum, m) => sum + balance(m.transactions), 0)

  function SortHeader({ sortKey, align, children }) {
    return (
      <TableCell align={align}>
        <TableSortLabel
          active={sort.key === sortKey}
          direction={sort.key === sortKey ? sort.dir : 'asc'}
          onClick={() => handleSort(sortKey)}
        >
          {children}
        </TableSortLabel>
      </TableCell>
    )
  }

  return (
    <TableContainer component={Paper} sx={{ mt: 1, mb: 3 }}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <SortHeader sortKey="category">Category</SortHeader>
            {year.months.map(m => (
              <TableCell key={m.index} align="right">
                <TableSortLabel
                  active={sort.key === String(m.index)}
                  direction={sort.key === String(m.index) ? sort.dir : 'asc'}
                  onClick={() => handleSort(String(m.index))}
                >
                  <Link to={`/transactions/${year.index}/${m.index}`} style={{ textDecoration: 'none' }}>
                    {MONTH_NAMES[m.index - 1]}
                  </Link>
                </TableSortLabel>
              </TableCell>
            ))}
            <SortHeader sortKey="total" align="right">Year total</SortHeader>
            <SortHeader sortKey="average" align="right">Year average</SortHeader>
          </TableRow>
        </TableHead>
        <TableBody>
          {sortedCategories.map(category => (
            <TableRow key={category} hover>
              <TableCell component="th" scope="row">{category}</TableCell>
              {year.months.map(m => (
                <TableCell key={m.index} align="right">
                  {fmt(monthTotal(m.index, category))}
                </TableCell>
              ))}
              <TableCell align="right"><strong>{fmt(yearTotal(category))}</strong></TableCell>
              <TableCell align="right"><strong>{fmt(yearAverage(category))}</strong></TableCell>
            </TableRow>
          ))}
        </TableBody>
        <TableFooter>
          <TableRow>
            <TableCell><strong>Balance</strong></TableCell>
            {year.months.map(m => (
              <TableCell key={m.index} align="right">
                <strong>{fmt(balance(m.transactions))}</strong>
              </TableCell>
            ))}
            <TableCell align="right"><strong>{fmt(yearBalance)}</strong></TableCell>
            <TableCell />
          </TableRow>
        </TableFooter>
      </Table>
    </TableContainer>
  )
}
