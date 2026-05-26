import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { CompanyDetail } from './pages/CompanyDetail'
import { Analysis } from './pages/Analysis'
import { Reports } from './pages/Reports'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="company/:ticker" element={<CompanyDetail />} />
        <Route path="analysis" element={<Analysis />} />
        <Route path="reports" element={<Reports />} />
      </Route>
    </Routes>
  )
}

export default App
