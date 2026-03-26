import { Container, Typography, Box, CircularProgress } from '@mui/material'
import { BarChart } from '@mui/x-charts/BarChart'
import { LineChart } from '@mui/x-charts/LineChart'
import { useFinances, totalAmount, allTransactions } from '../hooks/useFinances'
import { fmt } from '../utils/format'
import CategoryTable from '../components/CategoryTable'

const MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

export default function Summary() {
  const { data, loading, error } = useFinances()

  if (loading) return <Box sx={{ p: 4 }}><CircularProgress /></Box>
  if (error) return <Typography color="error" sx={{ p: 4 }}>Failed to load data: {error.message}</Typography>

  const { years, categories } = data

  const allYearsSeries = categories.map(cat => ({
    label: cat,
    data: years.map(y => totalAmount(allTransactions(y), cat)),
    stack: 'total',
    valueFormatter: fmt,
  }))

  const categoryAverageSeries = categories.map(cat => ({
    label: cat,
    data: years.map(y => {
      const total = totalAmount(allTransactions(y), cat)
      return y.months.length ? total / y.months.length : 0
    }),
    valueFormatter: fmt,
  }))

  const yearLabels = years.map(y => String(y.index))

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box sx={{ mb: 2 }}>
        <Typography component="span"><strong>Jump to: </strong></Typography>
        {[...years].reverse().map(y => (
          <Typography key={y.index} component="span" sx={{ mr: 1 }}>
            <a href={`#year-${y.index}`}>{y.index}</a>
          </Typography>
        ))}
      </Box>

      <Typography variant="h5" gutterBottom>Summary</Typography>
      <BarChart
        xAxis={[{ scaleType: 'band', data: yearLabels }]}
        series={allYearsSeries}
        height={400}
        slotProps={{ legend: { position: { vertical: 'middle', horizontal: 'right' } } }}
      />

      <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>Category averages over time</Typography>
      <LineChart
        xAxis={[{ scaleType: 'band', data: yearLabels }]}
        series={categoryAverageSeries}
        height={400}
        slotProps={{ legend: { position: { vertical: 'middle', horizontal: 'right' } } }}
      />

      {[...years].reverse().map(y => (
        <Box key={y.index} id={`year-${y.index}`} sx={{ mt: 5 }}>
          <Typography variant="h5" gutterBottom>{y.index}</Typography>
          <BarChart
            xAxis={[{ scaleType: 'band', data: MONTH_NAMES.slice(0, y.months.length) }]}
            series={categories.map(cat => ({
              label: cat,
              data: y.months.map(m => totalAmount(m.transactions, cat)),
              stack: 'total',
              valueFormatter: fmt,
            }))}
            height={300}
            slotProps={{ legend: { position: { vertical: 'middle', horizontal: 'right' } } }}
          />
          <CategoryTable year={y} categories={categories} />
        </Box>
      ))}
    </Container>
  )
}
