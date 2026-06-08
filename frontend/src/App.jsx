import { useState } from 'react'
import Login from './components/Login'
import Register from './components/Register'
import Home from './components/Home'
import './App.css'

function App() {
  const [page, setPage] = useState(() => {
    return localStorage.getItem('token') ? 'home' : 'login'
  })

  if (page === 'home') {
    return <Home onLogout={() => setPage('login')} />
  }

  if (page === 'register') {
    return (
      <Register
        onSwitch={() => setPage('login')}
        onRegistered={() => setPage('login')}
      />
    )
  }

  return (
    <Login
      onSwitch={() => setPage('register')}
      onSuccess={() => setPage('home')}
    />
  )
}

export default App
