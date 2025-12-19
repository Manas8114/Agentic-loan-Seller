import { useState, useRef, useEffect } from 'react'
import { Send, Paperclip, Bot, User, Loader2, CheckCircle2, FileUp, X } from 'lucide-react'
import clsx from 'clsx'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { chatApi, uploadApi, Message, ChatResponse } from '../services/api'

const stages = [
    { id: 'greeting', label: 'Welcome' },
    { id: 'need_analysis', label: 'Requirements' },
    { id: 'collecting_details', label: 'Details' },
    { id: 'kyc_verification', label: 'KYC' },
    { id: 'otp_verification', label: 'OTP' },
    { id: 'credit_check', label: 'Credit' },
    { id: 'salary_upload', label: 'Salary' },
    { id: 'underwriting', label: 'Underwriting' },
    { id: 'decision', label: 'Decision' },
    { id: 'scheme_recommendation', label: 'Schemes' },
    { id: 'rate_negotiation', label: 'Negotiation' },
    { id: 'sanction_letter', label: 'Sanction' },
]

export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([
        {
            role: 'assistant',
            content: "Hello! Welcome to our Personal Loan service. 👋\n\nI'm your AI assistant and I can help you:\n• Apply for a personal loan\n• Check your pre-approved limit\n• Calculate your EMI\n\nHow can I assist you today?",
            timestamp: new Date().toISOString(),
            agentType: 'master',
        },
    ])
    const [input, setInput] = useState('')
    const [conversationId, setConversationId] = useState<string | null>(null)
    const [applicationId, setApplicationId] = useState<string | null>(null)
    const [currentStage, setCurrentStage] = useState('greeting')
    const [isTyping, setIsTyping] = useState(false)
    const [isUploading, setIsUploading] = useState(false)
    const [selectedFile, setSelectedFile] = useState<File | null>(null)
    const messagesEndRef = useRef<HTMLDivElement>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const sendMessage = useMutation({
        mutationFn: async (message: string) => {
            return await chatApi.sendMessage(message, conversationId || undefined)
        },
        onMutate: async (message) => {
            // Add user message immediately
            const userMessage: Message = {
                role: 'user',
                content: message,
                timestamp: new Date().toISOString(),
            }
            setMessages((prev) => [...prev, userMessage])
            setInput('')
            setIsTyping(true)
        },
        onSuccess: (response: ChatResponse) => {
            setConversationId(response.conversation_id)
            setCurrentStage(response.stage)
            if (response.application_id) {
                setApplicationId(response.application_id)
            }

            const assistantMessage: Message = {
                role: 'assistant',
                content: response.message,
                timestamp: response.timestamp,
                agentType: response.agent_type,
            }
            setMessages((prev) => [...prev, assistantMessage])
            setIsTyping(false)
        },
        onError: (error) => {
            setIsTyping(false)
            toast.error('Failed to send message. Please try again.')
            console.error('Chat error:', error)
        },
    })

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (!input.trim() || sendMessage.isPending) return
        sendMessage.mutate(input.trim())
    }

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file) return

        // Validate file type
        const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg']
        if (!allowedTypes.includes(file.type)) {
            toast.error('Please upload a PDF or image file')
            return
        }

        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            toast.error('File size must be less than 5MB')
            return
        }

        // Validate application ID exists
        if (!applicationId) {
            toast.error('Please complete the application steps before uploading documents')
            return
        }

        setSelectedFile(file)
        setIsUploading(true)

        try {
            const result = await uploadApi.uploadFile(file, applicationId)

            // Add upload success message to chat
            const uploadMessage: Message = {
                role: 'user',
                content: `📎 Uploaded: ${file.name}`,
                timestamp: new Date().toISOString(),
            }
            setMessages((prev) => [...prev, uploadMessage])

            // Add system response
            const systemMessage: Message = {
                role: 'assistant',
                content: `✅ Document received! ${result.message || 'Processing your salary slip...'}

Monthly Net Salary: ₹${result.detected_salary?.toLocaleString('en-IN') || 'Processing...'}
Status: ${result.status || 'Uploaded'}`,
                timestamp: new Date().toISOString(),
                agentType: 'verification',
            }
            setMessages((prev) => [...prev, systemMessage])

            toast.success('File uploaded successfully!')
        } catch (error: any) {
            console.error('Upload error:', error)
            toast.error(error?.response?.data?.detail || 'Failed to upload file')
        } finally {
            setIsUploading(false)
            setSelectedFile(null)
            if (fileInputRef.current) {
                fileInputRef.current.value = ''
            }
        }
    }

    const getStageStatus = (stageId: string) => {
        const currentIndex = stages.findIndex((s) => s.id === currentStage)
        const stageIndex = stages.findIndex((s) => s.id === stageId)

        if (stageIndex < currentIndex) return 'completed'
        if (stageIndex === currentIndex) return 'current'
        return 'pending'
    }

    return (
        <div className="h-full flex flex-col lg:flex-row">
            {/* Stage tracker - Desktop */}
            <div className="hidden lg:block w-72 p-6 border-r border-dark-800 bg-dark-900/50">
                <h2 className="text-sm font-semibold text-dark-400 uppercase tracking-wider mb-6">
                    Application Progress
                </h2>

                <div className="space-y-4">
                    {stages.map((stage, index) => {
                        const status = getStageStatus(stage.id)

                        return (
                            <div key={stage.id} className="relative">
                                {index < stages.length - 1 && (
                                    <div
                                        className={clsx(
                                            'absolute left-4 top-10 w-0.5 h-8',
                                            status === 'completed' ? 'bg-green-500' : 'bg-dark-700'
                                        )}
                                    />
                                )}

                                <div className="flex items-center gap-3">
                                    <div
                                        className={clsx(
                                            'w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all',
                                            status === 'completed' && 'bg-green-500/20 border-green-500',
                                            status === 'current' && 'bg-primary-500/20 border-primary-500 animate-pulse',
                                            status === 'pending' && 'bg-dark-800 border-dark-600'
                                        )}
                                    >
                                        {status === 'completed' ? (
                                            <CheckCircle2 className="w-4 h-4 text-green-500" />
                                        ) : (
                                            <span
                                                className={clsx(
                                                    'text-xs font-medium',
                                                    status === 'current' ? 'text-primary-400' : 'text-dark-400'
                                                )}
                                            >
                                                {index + 1}
                                            </span>
                                        )}
                                    </div>

                                    <span
                                        className={clsx(
                                            'text-sm font-medium',
                                            status === 'completed' && 'text-green-400',
                                            status === 'current' && 'text-primary-400',
                                            status === 'pending' && 'text-dark-500'
                                        )}
                                    >
                                        {stage.label}
                                    </span>
                                </div>
                            </div>
                        )
                    })}
                </div>
            </div>

            {/* Chat area */}
            <div className="flex-1 flex flex-col h-[calc(100vh-4rem)] lg:h-screen">
                {/* Stage tracker - Mobile */}
                <div className="lg:hidden flex items-center gap-2 p-4 border-b border-dark-800 bg-dark-900/50 overflow-x-auto">
                    {stages.map((stage, index) => {
                        const status = getStageStatus(stage.id)

                        return (
                            <div
                                key={stage.id}
                                className={clsx(
                                    'flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap',
                                    status === 'completed' && 'bg-green-500/20 text-green-400',
                                    status === 'current' && 'bg-primary-500/20 text-primary-400',
                                    status === 'pending' && 'bg-dark-800 text-dark-500'
                                )}
                            >
                                {status === 'completed' ? (
                                    <CheckCircle2 className="w-3 h-3" />
                                ) : (
                                    <span>{index + 1}</span>
                                )}
                                {stage.label}
                            </div>
                        )
                    })}
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-4">
                    {messages.map((message, index) => (
                        <div
                            key={index}
                            className={clsx(
                                'flex gap-3 animate-in',
                                message.role === 'user' ? 'justify-end' : 'justify-start'
                            )}
                        >
                            {message.role === 'assistant' && (
                                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center flex-shrink-0">
                                    <Bot className="w-4 h-4 text-white" />
                                </div>
                            )}

                            <div
                                className={clsx(
                                    message.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-assistant'
                                )}
                            >
                                <div className="whitespace-pre-wrap">{message.content}</div>

                                {message.agentType && (
                                    <div className="mt-2 text-xs opacity-60 capitalize">
                                        via {message.agentType} agent
                                    </div>
                                )}
                            </div>

                            {message.role === 'user' && (
                                <div className="w-8 h-8 rounded-full bg-dark-700 flex items-center justify-center flex-shrink-0">
                                    <User className="w-4 h-4 text-dark-300" />
                                </div>
                            )}
                        </div>
                    ))}

                    {isTyping && (
                        <div className="flex gap-3 justify-start animate-in">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center flex-shrink-0">
                                <Bot className="w-4 h-4 text-white" />
                            </div>
                            <div className="chat-bubble-assistant">
                                <div className="typing-indicator">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <div className="p-4 lg:p-6 border-t border-dark-800 bg-dark-900/50">
                    {/* Selected file preview */}
                    {selectedFile && (
                        <div className="mb-3 p-2 bg-dark-800 rounded-lg flex items-center justify-between">
                            <div className="flex items-center gap-2 text-sm text-dark-300">
                                <FileUp className="w-4 h-4 text-primary-400" />
                                <span>{selectedFile.name}</span>
                            </div>
                            <button
                                type="button"
                                onClick={() => {
                                    setSelectedFile(null)
                                    if (fileInputRef.current) fileInputRef.current.value = ''
                                }}
                                className="text-dark-400 hover:text-white"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="flex items-center gap-3">
                        {/* Hidden file input */}
                        <input
                            type="file"
                            ref={fileInputRef}
                            onChange={handleFileSelect}
                            accept=".pdf,.jpg,.jpeg,.png"
                            className="hidden"
                        />

                        <button
                            type="button"
                            onClick={() => fileInputRef.current?.click()}
                            disabled={isUploading}
                            className={clsx(
                                "p-3 rounded-xl transition-all",
                                isUploading
                                    ? "bg-primary-500/20 text-primary-400 animate-pulse"
                                    : "text-dark-400 hover:bg-dark-800 hover:text-white"
                            )}
                        >
                            {isUploading ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <Paperclip className="w-5 h-5" />
                            )}
                        </button>

                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Type your message..."
                            className="input-primary flex-1"
                            disabled={sendMessage.isPending}
                        />

                        <button
                            type="submit"
                            disabled={!input.trim() || sendMessage.isPending}
                            className={clsx(
                                'p-3 rounded-xl transition-all',
                                input.trim() && !sendMessage.isPending
                                    ? 'bg-primary-500 text-white hover:bg-primary-400'
                                    : 'bg-dark-800 text-dark-500 cursor-not-allowed'
                            )}
                        >
                            {sendMessage.isPending ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <Send className="w-5 h-5" />
                            )}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    )
}
