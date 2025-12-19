import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { MessageSquare, LayoutDashboard, LogOut, Moon, Sun, Menu } from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'
import { useAuth } from '../context/AuthContext'

const navItems = [
    { path: '/', label: 'Chat', icon: MessageSquare },
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
]

export default function Layout() {
    const location = useLocation()
    const navigate = useNavigate()
    const { logout } = useAuth()
    const [sidebarOpen, setSidebarOpen] = useState(false)
    const [darkMode, setDarkMode] = useState(true)

    const handleLogout = () => {
        logout()
        navigate('/login')
    }

    return (
        <div className="min-h-screen bg-dark-950 flex">
            {/* Sidebar */}
            <aside
                className={clsx(
                    'fixed inset-y-0 left-0 z-50 w-64 bg-dark-900/95 backdrop-blur-xl border-r border-dark-800 transform transition-transform duration-300 lg:translate-x-0 lg:static',
                    sidebarOpen ? 'translate-x-0' : '-translate-x-full'
                )}
            >
                <div className="flex flex-col h-full">
                    {/* Logo */}
                    <div className="p-6 border-b border-dark-800">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
                                <span className="text-white font-bold text-lg">A</span>
                            </div>
                            <div>
                                <h1 className="font-bold text-white">Agentic</h1>
                                <p className="text-xs text-dark-400">Loan Assistant</p>
                            </div>
                        </div>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 p-4 space-y-2">
                        {navItems.map((item) => {
                            const isActive = location.pathname === item.path
                            const Icon = item.icon

                            return (
                                <Link
                                    key={item.path}
                                    to={item.path}
                                    onClick={() => setSidebarOpen(false)}
                                    className={clsx(
                                        'flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-all duration-200',
                                        isActive
                                            ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                                            : 'text-dark-300 hover:bg-dark-800 hover:text-white'
                                    )}
                                >
                                    <Icon className="w-5 h-5" />
                                    {item.label}
                                </Link>
                            )
                        })}
                    </nav>

                    {/* Bottom */}
                    <div className="p-4 border-t border-dark-800 space-y-2">
                        <button
                            onClick={() => setDarkMode(!darkMode)}
                            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-dark-300 hover:bg-dark-800 hover:text-white transition-all"
                        >
                            {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                            {darkMode ? 'Light Mode' : 'Dark Mode'}
                        </button>

                        <button
                            onClick={handleLogout}
                            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-red-400 hover:bg-red-500/10 transition-all"
                        >
                            <LogOut className="w-5 h-5" />
                            Logout
                        </button>
                    </div>
                </div>
            </aside>

            {/* Mobile overlay */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 lg:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Main content */}
            <div className="flex-1 flex flex-col min-h-screen">
                {/* Mobile header */}
                <header className="lg:hidden flex items-center justify-between p-4 border-b border-dark-800 bg-dark-900/80 backdrop-blur-xl">
                    <button
                        onClick={() => setSidebarOpen(true)}
                        className="p-2 rounded-lg hover:bg-dark-800"
                    >
                        <Menu className="w-6 h-6 text-dark-200" />
                    </button>

                    <h1 className="font-bold text-white">Agentic Loan</h1>

                    <div className="w-10" />
                </header>

                {/* Page content */}
                <main className="flex-1 overflow-hidden">
                    <Outlet />
                </main>
            </div>
        </div>
    )
}
