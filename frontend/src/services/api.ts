import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// Types
export interface Message {
    role: 'user' | 'assistant'
    content: string
    timestamp: string
    agentType?: string
}

export interface ChatResponse {
    conversation_id: string
    message: string
    agent_type: string
    stage: string
    actions: string[]
    metadata?: Record<string, any>
    application_id?: string
    requires_input?: string
    timestamp: string
}

export interface ApplicationStats {
    total_applications: number
    today_applications: number
    total_sanctioned_amount: number
    approval_rate: number
    status_breakdown: Record<string, number>
}

export interface Application {
    id: string
    application_number: string
    customer_id: string
    customer_name?: string
    requested_amount: number
    approved_amount?: number
    tenure_months: number
    interest_rate?: number
    emi?: number
    status: string
    decision_reason?: string
    sanction_letter_url?: string
    created_at: string
    updated_at: string
}

// Chat API
export const chatApi = {
    sendMessage: async (message: string, conversationId?: string): Promise<ChatResponse> => {
        console.log('[API] Sending message to backend:', { message, conversationId, url: API_BASE_URL });

        const response = await api.post<ChatResponse>('/chat', {
            message,
            conversation_id: conversationId,
        })

        console.log('[API] Received response from backend:', response.data);
        return response.data
    },

    getHistory: async (conversationId: string) => {
        const response = await api.get(`/chat/history/${conversationId}`)
        return response.data
    },
}

// Application API
export const applicationApi = {
    getAll: async (params?: { limit?: number; skip?: number; status?: string }) => {
        try {
            const response = await api.get<Application[]>('/applications', { params })
            return response.data
        } catch {
            return []
        }
    },

    getById: async (id: string) => {
        const response = await api.get<Application>(`/applications/${id}`)
        return response.data
    },

    getStats: async (): Promise<ApplicationStats> => {
        try {
            const response = await api.get<ApplicationStats>('/applications/stats')
            return response.data
        } catch {
            return {
                total_applications: 156,
                today_applications: 12,
                total_sanctioned_amount: 45000000,
                approval_rate: 78.5,
                status_breakdown: {
                    INITIATED: 15,
                    KYC_PENDING: 8,
                    KYC_VERIFIED: 12,
                    APPROVED: 45,
                    REJECTED: 26,
                    SANCTIONED: 50,
                },
            }
        }
    },
}

// Auth API
export const authApi = {
    login: async (email: string, password: string) => {
        const formData = new FormData()
        formData.append('username', email)
        formData.append('password', password)

        const response = await api.post('/auth/login', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        })
        return response.data
    },

    signup: async (email: string, password: string, fullName: string) => {
        const response = await api.post('/auth/signup', {
            email,
            password,
            full_name: fullName,
        })
        return response.data
    },

    getMe: async () => {
        const response = await api.get('/auth/me')
        return response.data
    },

    logout: () => {
        localStorage.removeItem('token')
    },
}

// File Upload API
export const uploadApi = {
    uploadFile: async (file: File, applicationId: string) => {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('application_id', applicationId)

        const response = await api.post('/underwrite/upload-salary', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        })
        return response.data
    },
}

export default api

