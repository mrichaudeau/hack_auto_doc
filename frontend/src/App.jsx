import { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="App">
      <header className="App-header">
        <h1>Plateforme de Veille Technologique IA</h1>
        <p>
          Système de surveillance technologique alimenté par l'IA
        </p>
        <div className="card">
          <button onClick={() => setCount((count) => count + 1)}>
            count is {count}
          </button>
          <p>
            Modifiez <code>src/App.jsx</code> et enregistrez pour tester le HMR
          </p>
        </div>
      </header>
    </div>
  )
}

export default App
