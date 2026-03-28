import { Link } from 'react-router-dom'
import { Box } from '@mui/material'
import { DataGrid } from '@mui/x-data-grid'
import { totalAmount, balance } from '../hooks/useFinances'
import { fmt } from '../utils/format'

const MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

export default function CategoryTable({ year, categories }) {
  // Build row data: one row per category with precomputed month totals
  const rows = categories.map(category => {
    const row = { id: category, category }
    year.months.forEach(m => {
      row[String(m.index)] = totalAmount(m.transactions, category)
    })
    row.total = year.months.reduce((sum, m) => sum + totalAmount(m.transactions, category), 0)
    row.average = year.months.length === 0 ? 0 : row.total / year.months.length
    return row
  })

  // Precompute balance per month for footer
  const monthBalances = Object.fromEntries(
    year.months.map(m => [String(m.index), balance(m.transactions)])
  )
  const yearBalance = year.months.reduce((sum, m) => sum + balance(m.transactions), 0)

  // Build column definitions
  const columns = [
    { field: 'category', headerName: 'Category', width: 180 },
    ...year.months.map(m => ({
      field: String(m.index),
      type: 'number',
      width: 80,
      valueFormatter: (value) => fmt(value),
      renderHeader: () => (
        <Link
          to={`/transactions/${year.index}/${m.index}`}
          style={{ textDecoration: 'none', color: 'inherit' }}
        >
          {MONTH_NAMES[m.index - 1]}
        </Link>
      ),
    })),
    {
      field: 'total',
      headerName: 'Year total',
      type: 'number',
      width: 110,
      valueFormatter: (value) => fmt(value),
    },
    {
      field: 'average',
      headerName: 'Year avg',
      type: 'number',
      width: 110,
      valueFormatter: (value) => fmt(value),
    },
  ]

  function BalanceFooter() {
    return (
      <Box sx={{ display: 'flex', px: 1, py: 0.5, borderTop: 1, borderColor: 'divider', typography: 'body2' }}>
        <Box sx={{ width: 180, fontWeight: 'bold' }}>Balance</Box>
        {year.months.map(m => (
          <Box key={m.index} sx={{ width: 80, textAlign: 'right' }}>
            {fmt(monthBalances[String(m.index)])}
          </Box>
        ))}
        <Box sx={{ width: 110, textAlign: 'right', fontWeight: 'bold' }}>{fmt(yearBalance)}</Box>
        <Box sx={{ width: 110 }} />
      </Box>
    )
  }

  return (
    <DataGrid
      rows={rows}
      columns={columns}
      autoHeight
      disableRowSelectionOnClick
      hideFooterPagination
      hideFooterSelectedRowCount
      slots={{ footer: BalanceFooter }}
      initialState={{
        sorting: { sortModel: [{ field: 'category', sort: 'asc' }] },
      }}
      sx={{ mt: 1, mb: 3 }}
    />
  )
}
