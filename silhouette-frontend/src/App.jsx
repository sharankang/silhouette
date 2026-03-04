import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/UI/Layout'
import WardrobePage from './pages/WardrobePage'
import ChatPage from './pages/ChatPage'
import OutfitsPage from './pages/OutfitsPage'
import MixPage from './pages/MixPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/wardrobe" replace />} />
        <Route path="wardrobe" element={<WardrobePage />} />
        <Route path="chat"     element={<ChatPage />} />
        <Route path="outfits"  element={<OutfitsPage />} />
        <Route path="mix"      element={<MixPage />} />
      </Route>
    </Routes>
  )
}