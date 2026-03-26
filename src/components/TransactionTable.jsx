import { useState } from 'react'
import {
  Box, Table, TableBody, TableCell, TableContainer, TableHead,
  TableRow, TableSortLabel, Paper, TextField,
} from '@mui/material'
import { fmt } from '../utils/format'

const COLUMNS = [
  { key: 'date',        label: 'Date' },
  { key: 'type',        label: 'Type' },
  { key: 'category',    label: 'Category' },
  { key: 'description', label: 'Description' },
  { key: 'amount',      label: 'Amount', align: 'right' },
  { key: 'note',        label: 'Note' },
]

export default function TransactionTable({ transactions }) {
  const [filter, setFilter] = useState('')
  const [sort, setSort] = useState({ key: 'date', dir: 'asc' })

  function handleSort(key) {
    setSort(s => s.key === key
      ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' }
      : { key, dir: 'asc' }
    )
  }

  const filtered = filter
    ? transactions.filter(t =>
        Object.values(t).some(v =>
          String(v).toLowerCase().includes(filter.toLowerCase())
        )
      )
    : transactions

  const sorted = [...filtered].sort((a, b) => {
    const dir = sort.dir === 'asc' ? 1 : -1
    if (sort.key === 'amount') return dir * (a.amount - b.amount)
    return dir * String(a[sort.key]).localeCompare(String(b[sort.key]))
  })

  return (
    <Box>
      <TextField
        label="Filter"
        value={filter}
        onChange={e => setFilter(e.target.value)}
        size="small"
        sx={{ mb: 2 }}
      />
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              {COLUMNS.map(col => (
                <TableCell key={col.key} align={col.align}>
                  <TableSortLabel
                    active={sort.key === col.key}
                    direction={sort.key === col.key ? sort.dir : 'asc'}
                    onClick={() => handleSort(col.key)}
                  >
                    {col.label}
                  </TableSortLabel>
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {sorted.map((t, i) => (
              <TableRow key={i} hover>
                <TableCell>{t.date}</TableCell>
                <TableCell>{t.type}</TableCell>
                <TableCell>{t.category}</TableCell>
                <TableCell>{t.description}</TableCell>
                <TableCell align="right">{fmt(t.amount)}</TableCell>
                <TableCell>{t.note}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
