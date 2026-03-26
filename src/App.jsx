import { HashRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider, createTheme, CssBaseline, AppBar, Toolbar, Typography } from '@mui/material'
import Summary from './pages/Summary'
import MonthDetail from './pages/MonthDetail'

const theme = createTheme()

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <HashRouter>
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div">
              Finances
            </Typography>
          </Toolbar>
        </AppBar>
        <Routes>
          <Route path="/" element={<Summary />} />
          <Route path="/transactions/:year/:month" element={<MonthDetail />} />
        </Routes>
      </HashRouter>
    </ThemeProvider>
  )
}
