import { DataGrid, GridToolbar } from '@mui/x-data-grid'
import { fmt } from '../utils/format'

const COLUMNS = [
  { field: 'date',        headerName: 'Date',        width: 110 },
  { field: 'type',        headerName: 'Type',        width: 70 },
  { field: 'category',    headerName: 'Category',    width: 160 },
  { field: 'description', headerName: 'Description', flex: 1 },
  {
    field: 'amount',
    headerName: 'Amount',
    type: 'number',
    width: 110,
    valueFormatter: (value) => fmt(value),
  },
  { field: 'note', headerName: 'Note', flex: 1 },
]

export default function TransactionTable({ transactions }) {
  const rows = transactions.map((t, i) => ({ id: i, ...t }))

  return (
    <DataGrid
      rows={rows}
      columns={COLUMNS}
      autoHeight
      disableRowSelectionOnClick
      slots={{ toolbar: GridToolbar }}
      slotProps={{ toolbar: { showQuickFilter: true } }}
      initialState={{
        sorting: { sortModel: [{ field: 'date', sort: 'asc' }] },
      }}
    />
  )
}
