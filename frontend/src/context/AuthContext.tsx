import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authApi } from '../services/api'

interface User {
    id: string
    email: string
    full_name: string
    role: string
}

interface AuthContextType {
    user: User | null
    token: string | null
    isAuthenticated: boolean
    isLoading: boolean
    login: (email: string, password: string) => Promise<void>
    signup: (email: string, password: string, fullName: string) => Promise<void>
    logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null)
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        // Check for existing token on app load - token already initialized from localStorage
        if (token) {
            // Fetch user info
            authApi.getMe()
                .then(userData => {
                    setUser(userData)
                })
                .catch(() => {
                    // Token invalid, clear it
                    localStorage.removeItem('token')
                    setToken(null)
                })
                .finally(() => {
                    setIsLoading(false)
                })
        } else {
            setIsLoading(false)
        }
    }, [])

    const login = async (email: string, password: string) => {
        const response = await authApi.login(email, password)
        localStorage.setItem('token', response.access_token)
        setToken(response.access_token)

        // Fetch user info after login
        const userData = await authApi.getMe()
        setUser(userData)
    }

    const signup = async (email: string, password: string, fullName: string) => {
        await authApi.signup(email, password, fullName)
    }

    const logout = () => {
        localStorage.removeItem('token')
        setToken(null)
        setUser(null)
    }

    return (
        <AuthContext.Provider
            value={{
                user,
                token,
                isAuthenticated: !!token,
                isLoading,
                login,
                signup,
                logout,
            }}
        >
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const context = useContext(AuthContext)
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}
