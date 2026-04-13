/* Monta a raiz React e aplica estilos globais. */
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import PainelCatalogo from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <PainelCatalogo />
  </StrictMode>,
)
