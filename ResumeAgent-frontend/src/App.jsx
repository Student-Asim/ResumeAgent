import { useState } from 'react'
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom'
import UploadPage from './pages/UploadPage'
import ResultsPage from './pages/ResultsPage'
import PracticePage from './pages/PracticePage'

// This component holds the state shared between pages
function AppInner() {
  const [result, setResult] = useState(null)   // stores /analyze-full response
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  // Called by UploadPage when analysis is done
  const handleResult = (data) => {
    setResult(data)
    navigate('/results')   // automatically navigates to results page
  }

  return (
    <Routes>
      <Route
        path="/"
        element={
          <UploadPage
            loading={loading}
            setLoading={setLoading}
            onResult={handleResult}
          />
        }
      />
      <Route
        path="/results"
        element={<ResultsPage result={result} />}
      />
      <Route
        path="/practice"
        element={<PracticePage sessionId={result?.session_id} />}
      />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppInner />
    </BrowserRouter>
  )
}