import { useQuery } from '@tanstack/react-query'
import {
    TrendingUp,
    Users,
    IndianRupee,
    Clock,
    RefreshCw
} from 'lucide-react'
import clsx from 'clsx'
import { applicationApi, ApplicationStats, Application } from '../services/api'

const statusColors: Record<string, string> = {
    INITIATED: 'bg-gray-500/20 text-gray-400',
    KYC_PENDING: 'bg-yellow-500/20 text-yellow-400',
    KYC_VERIFIED: 'bg-blue-500/20 text-blue-400',
    APPROVED: 'bg-green-500/20 text-green-400',
    REJECTED: 'bg-red-500/20 text-red-400',
    SANCTIONED: 'bg-purple-500/20 text-purple-400',
}

export default function DashboardPage() {
    const { data: stats, refetch } = useQuery({
        queryKey: ['applicationStats'],
        queryFn: applicationApi.getStats,
        // Use mock data if API fails
        placeholderData: {
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
        } as ApplicationStats,
    })

    const { data: applications } = useQuery<Application[]>({
        queryKey: ['applications'],
        queryFn: () => applicationApi.getAll({ limit: 10 }),
        // Mock data
        placeholderData: [
            { id: '1', application_number: 'LA20241212001', customer_id: 'cust1', customer_name: 'Rajesh Sharma', status: 'SANCTIONED', requested_amount: 500000, tenure_months: 36, created_at: '2024-12-12T10:00:00Z', updated_at: '2024-12-12T10:00:00Z' },
            { id: '2', application_number: 'LA20241212002', customer_id: 'cust2', customer_name: 'Priya Patel', status: 'APPROVED', requested_amount: 300000, tenure_months: 24, created_at: '2024-12-12T11:30:00Z', updated_at: '2024-12-12T11:30:00Z' },
            { id: '3', application_number: 'LA20241212003', customer_id: 'cust3', customer_name: 'Amit Singh', status: 'KYC_VERIFIED', requested_amount: 750000, tenure_months: 48, created_at: '2024-12-12T12:15:00Z', updated_at: '2024-12-12T12:15:00Z' },
            { id: '4', application_number: 'LA20241212004', customer_id: 'cust4', customer_name: 'Sneha Reddy', status: 'REJECTED', requested_amount: 1000000, tenure_months: 60, created_at: '2024-12-12T13:00:00Z', updated_at: '2024-12-12T13:00:00Z' },
            { id: '5', application_number: 'LA20241212005', customer_id: 'cust5', customer_name: 'Vikram Mehta', status: 'KYC_PENDING', requested_amount: 200000, tenure_months: 12, created_at: '2024-12-12T14:30:00Z', updated_at: '2024-12-12T14:30:00Z' },
        ],
    })

    const statCards = [
        {
            label: 'Total Applications',
            value: stats?.total_applications || 0,
            icon: Users,
            color: 'from-blue-500 to-blue-600',
        },
        {
            label: 'Today',
            value: stats?.today_applications || 0,
            icon: Clock,
            color: 'from-purple-500 to-purple-600',
        },
        {
            label: 'Total Sanctioned',
            value: `₹${((stats?.total_sanctioned_amount || 0) / 10000000).toFixed(1)}Cr`,
            icon: IndianRupee,
            color: 'from-green-500 to-green-600',
        },
        {
            label: 'Approval Rate',
            value: `${stats?.approval_rate || 0}%`,
            icon: TrendingUp,
            color: 'from-amber-500 to-amber-600',
        },
    ]

    return (
        <div className="h-full overflow-y-auto p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">Dashboard</h1>
                    <p className="text-dark-400 mt-1">Loan applications overview</p>
                </div>

                <button
                    onClick={() => refetch()}
                    className="btn-secondary flex items-center gap-2"
                >
                    <RefreshCw className="w-4 h-4" />
                    Refresh
                </button>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {statCards.map((stat, index) => {
                    const Icon = stat.icon

                    return (
                        <div
                            key={index}
                            className="card relative overflow-hidden group hover:border-primary-500/30 transition-all"
                        >
                            <div className={clsx(
                                'absolute inset-0 opacity-5 bg-gradient-to-br',
                                stat.color
                            )} />

                            <div className="relative">
                                <div className="flex items-center justify-between mb-4">
                                    <div className={clsx(
                                        'w-12 h-12 rounded-xl bg-gradient-to-br flex items-center justify-center',
                                        stat.color
                                    )}>
                                        <Icon className="w-6 h-6 text-white" />
                                    </div>
                                </div>

                                <div className="space-y-1">
                                    <p className="text-2xl font-bold text-white">{stat.value}</p>
                                    <p className="text-sm text-dark-400">{stat.label}</p>
                                </div>
                            </div>
                        </div>
                    )
                })}
            </div>

            {/* Status Breakdown */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Status chart */}
                <div className="card lg:col-span-1">
                    <h3 className="font-semibold text-white mb-4">Status Breakdown</h3>

                    <div className="space-y-3">
                        {stats?.status_breakdown && Object.entries(stats.status_breakdown).map(([status, count]) => {
                            const total = stats.total_applications || 1
                            const percentage = ((count as number) / total) * 100

                            return (
                                <div key={status}>
                                    <div className="flex items-center justify-between text-sm mb-1">
                                        <span className="text-dark-300">{status.replace(/_/g, ' ')}</span>
                                        <span className="text-dark-400">{count as number}</span>
                                    </div>
                                    <div className="h-2 bg-dark-800 rounded-full overflow-hidden">
                                        <div
                                            className={clsx(
                                                'h-full rounded-full transition-all duration-500',
                                                status.includes('APPROVED') || status.includes('SANCTIONED')
                                                    ? 'bg-green-500'
                                                    : status.includes('REJECTED')
                                                        ? 'bg-red-500'
                                                        : 'bg-primary-500'
                                            )}
                                            style={{ width: `${percentage}%` }}
                                        />
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>

                {/* Recent Applications */}
                <div className="card lg:col-span-2">
                    <h3 className="font-semibold text-white mb-4">Recent Applications</h3>

                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="text-left text-dark-400 text-sm border-b border-dark-800">
                                    <th className="pb-3 font-medium">Application</th>
                                    <th className="pb-3 font-medium">Customer</th>
                                    <th className="pb-3 font-medium">Amount</th>
                                    <th className="pb-3 font-medium">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-dark-800">
                                {applications?.map((app: Application) => (
                                    <tr key={app.id} className="text-sm">
                                        <td className="py-3">
                                            <span className="text-primary-400 font-mono">
                                                {app.application_number}
                                            </span>
                                        </td>
                                        <td className="py-3 text-dark-200">
                                            {app.customer_name}
                                        </td>
                                        <td className="py-3 text-dark-200">
                                            ₹{(app.requested_amount / 100000).toFixed(1)}L
                                        </td>
                                        <td className="py-3">
                                            <span className={clsx(
                                                'badge',
                                                statusColors[app.status] || 'bg-dark-700 text-dark-300'
                                            )}>
                                                {app.status.replace(/_/g, ' ')}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    )
}
