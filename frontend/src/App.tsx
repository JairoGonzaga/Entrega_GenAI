import './App.css'
import { useState } from 'react'
import CatalogPage from './features/catalog/CatalogPage'
import AIAnalystPage from './features/analyst/AIAnalystPage'

type AppTab = 'catalogo' | 'analista'

export default function App() {
	const [tab, setTab] = useState<AppTab>('catalogo')

	return (
		<div className="app-shell">
			<header className="top-nav">
				<div>
					<p className="eyebrow">Painel Gerencial</p>
					<h1>E-Commerce Workspace</h1>
				</div>

				<nav className="tab-switch" aria-label="Abas principais do painel">
					<button
						type="button"
						className={tab === 'catalogo' ? 'active' : ''}
						onClick={() => setTab('catalogo')}
					>
						Catalogo
					</button>
					<button
						type="button"
						className={tab === 'analista' ? 'active' : ''}
						onClick={() => setTab('analista')}
					>
						Analista IA
					</button>
				</nav>
			</header>

			{tab === 'catalogo' ? <CatalogPage /> : <AIAnalystPage />}
		</div>
	)
}
