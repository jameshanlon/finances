import { useParams, Link } from 'react-router-dom'
import { Container, Typography, Box, CircularProgress, Button } from '@mui/material'
import { PieChart } from '@mui/x-charts/PieChart'
import { useFinances, balance } from '../hooks/useFinances'
import { fmt } from '../utils/format'
import TransactionTable from '../components/TransactionTable'

const MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

export default function MonthDetail() {
  const { year: yearParam, month: monthParam } = useParams()
  const { data, loading, error } = useFinances()

  if (loading) return <Box sx={{ p: 4 }}><CircularProgress /></Box>
  if (error) return <Typography color="error" sx={{ p: 4 }}>Failed to load data: {error.message}</Typography>

  const yearIndex = parseInt(yearParam)
  const monthIndex = parseInt(monthParam)
  const year = data.years.find(y => y.index === yearIndex)
  const month = year?.months.find(m => m.index === monthIndex)
  const transactions = month?.transactions ?? []

  const pieData = data.categories
    .filter(cat => cat !== 'INCOME')
    .map((cat, i) => ({
      id: i,
      label: cat,
      value: transactions
        .filter(t => t.category === cat)
        .reduce((sum, t) => sum + t.amount, 0),
    }))
    .filter(d => d.value > 0)

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Button component={Link} to="/" sx={{ mb: 2 }}>← Back to summary</Button>

      <Typography variant="h5" gutterBottom>
        Transactions — {MONTH_NAMES[monthIndex - 1]} {yearIndex}
      </Typography>
      <Typography>Balance: {fmt(balance(transactions))}</Typography>
      <Typography sx={{ mb: 2 }}>{transactions.length} transactions</Typography>

      {pieData.length > 0 && (
        <Box sx={{ width: 600, mb: 3 }}>
          <PieChart
            series={[{
              data: pieData,
              valueFormatter: v => fmt(v.value),
            }]}
            height={300}
            slotProps={{ legend: { position: { vertical: 'middle', horizontal: 'right' } } }}
          />
        </Box>
      )}

      <TransactionTable transactions={transactions} />
    </Container>
  )
}
