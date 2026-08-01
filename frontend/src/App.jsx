import { MemoryRouter } from 'react-router-dom'
import ComponentPreview from './pages/ComponentPreview'

// TEMPORARY: swapped in for the Phase 1 component smoke test.
// Real routing (Phase 2) will replace this with <RouterProvider>/<Routes>.
function App() {
  return (
    <MemoryRouter>
      <ComponentPreview />
    </MemoryRouter>
  )
}

export default App
