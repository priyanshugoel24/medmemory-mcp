'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { api } from '../lib/api'
import LoadingSpinner from '../components/LoadingSpinner'

type DashboardData = {
  medication_count: number
  marker_count: number
  abnormal_lab: {
    marker_name: string
    value: number
    unit: string | null
    reference_min: number | null
    reference_max: number | null
    test_date: string
  } | null
  pending_followups: {
    from_visit: string | null
    doctor: string | null
    follow_up: string
  }[]
  overdue_vaccine_count: number
  vaccination_gap_count: number
  recent_documents: {
    id: number
    file_name: string
    ingested_at: string
    what_was_found: string
  }[]
}

const QUICK_LINKS = [
  { href: '/upload', label: 'Upload a document', description: 'Add a prescription, lab report, or record' },
  { href: '/medications', label: 'View medications', description: 'See everything you are currently taking' },
  { href: '/labs', label: 'Explore lab trends', description: 'Track a marker over time' },
  { href: '/summary', label: 'Health summary', description: 'A printable overview for your doctor' },
]

function formatTimeAgo(testDateStr: string) {
  if (!testDateStr) return ''
  const testDate = new Date(testDateStr)
  const now = new Date()
  const yearsDiff = now.getFullYear() - testDate.getFullYear()
  const monthsDiff = now.getMonth() - testDate.getMonth() + (yearsDiff * 12)
  
  if (monthsDiff <= 0) {
    return 'recently'
  } else if (monthsDiff === 1) {
    return '1 month ago'
  } else {
    return `${monthsDiff} months ago`
  }
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get('/dashboard')
      .then((res) => {
        setData(res.data)
      })
      .catch((err) => {
        console.error('Failed to load dashboard data', err)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <main className="max-w-5xl mx-auto px-6 py-10">
        <LoadingSpinner />
      </main>
    )
  }

  if (!data) {
    return (
      <main className="max-w-5xl mx-auto px-6 py-10">
        <div className="text-center py-12 text-gray-500 dark:text-zinc-400">
          Failed to load dashboard data. Please verify the API server is running.
        </div>
      </main>
    )
  }

  return (
    <main className="max-w-5xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">
          Welcome back
        </h1>
        <p className="text-gray-500 dark:text-zinc-400 mt-1">
          Here&apos;s a snapshot of your health record.
        </p>
      </div>

      {/* Vaccination Gap Banner */}
      {data.overdue_vaccine_count > 0 && (
        <Link
          href="/summary"
          className="mb-8 flex items-center justify-between p-4 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/50 rounded-xl text-amber-800 dark:text-amber-300 hover:bg-amber-100/30 dark:hover:bg-amber-950/30 transition-all duration-150 shadow-sm"
        >
          <div className="flex items-center gap-3">
            <svg
              className="w-5 h-5 flex-shrink-0 text-amber-600 dark:text-amber-400"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth="2"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <span className="font-medium text-sm">
              {data.overdue_vaccine_count} vaccine{data.overdue_vaccine_count > 1 ? 's' : ''} overdue — check your vaccination status.
            </span>
          </div>
          <div className="flex items-center gap-1 text-xs font-semibold uppercase tracking-wider text-amber-900 dark:text-amber-200">
            Check Status
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
          </div>
        </Link>
      )}

      {/* Quick Action Buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        <Link
          href="/upload"
          className="flex items-center gap-4 p-5 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-xl hover:border-emerald-500 dark:hover:border-emerald-500 hover:shadow-sm transition-all duration-150 group"
        >
          <div className="p-3 bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400 rounded-lg group-hover:bg-emerald-100 dark:group-hover:bg-emerald-950/40 transition-colors">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v6m3-3H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white text-sm">Upload a document</h3>
            <p className="text-xs text-gray-500 dark:text-zinc-400 mt-0.5">Add a prescription, lab report, or record</p>
          </div>
        </Link>

        <Link
          href="/summary"
          className="flex items-center gap-4 p-5 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-xl hover:border-indigo-500 dark:hover:border-indigo-500 hover:shadow-sm transition-all duration-150 group"
        >
          <div className="p-3 bg-indigo-50 dark:bg-indigo-950/20 text-indigo-600 dark:text-indigo-400 rounded-lg group-hover:bg-indigo-100 dark:group-hover:bg-indigo-950/40 transition-colors">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white text-sm">Generate health summary</h3>
            <p className="text-xs text-gray-500 dark:text-zinc-400 mt-0.5">A printable overview for your doctor</p>
          </div>
        </Link>
      </div>

      {/* Summary Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mb-10">
        {/* Medication Card */}
        <Link
          href="/medications"
          className="rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 hover:border-gray-300 dark:hover:border-zinc-700 transition-all duration-150 shadow-sm flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300">
                Active
              </span>
              <svg className="w-5 h-5 text-emerald-600 dark:text-emerald-400" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v-7.5m-3-3h6M12 3a9 9 0 000 18 9 9 0 000-18z" />
              </svg>
            </div>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-3 tabular-nums">
              {data.medication_count}
            </p>
          </div>
          <p className="text-xs text-gray-500 dark:text-zinc-400 mt-4 font-medium leading-snug">
            Active medications
          </p>
        </Link>

        {/* Lab alert card */}
        {data.abnormal_lab ? (
          <Link
            href="/labs"
            className="rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50/20 dark:bg-red-950/10 p-5 hover:border-red-300 dark:hover:border-red-800 hover:bg-red-50/30 dark:hover:bg-red-950/15 transition-all duration-150 shadow-sm flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-300">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-600 dark:bg-red-400 animate-pulse"></span>
                  Alert
                </span>
                <svg className="w-5 h-5 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <p className="text-base font-semibold text-gray-900 dark:text-white mt-3 leading-snug">
                {data.abnormal_lab.marker_name} is {data.abnormal_lab.value}{data.abnormal_lab.unit}
              </p>
              <p className="text-xs text-red-600 dark:text-red-400 font-medium mt-1 leading-snug">
                Above reference range
              </p>
            </div>
            <p className="text-[11px] text-gray-400 dark:text-zinc-500 mt-4 leading-snug">
              Checked {formatTimeAgo(data.abnormal_lab.test_date)}
            </p>
          </Link>
        ) : (
          <Link
            href="/labs"
            className="rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 hover:border-gray-300 dark:hover:border-zinc-700 transition-all duration-150 shadow-sm flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300">
                  Normal
                </span>
                <svg className="w-5 h-5 text-emerald-600 dark:text-emerald-400" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-3 tabular-nums">
                {data.marker_count}
              </p>
            </div>
            <p className="text-xs text-gray-500 dark:text-zinc-400 mt-4 font-medium leading-snug">
              Lab markers tracked
            </p>
          </Link>
        )}

        {/* Upcoming followups */}
        <Link
          href="/summary"
          className="rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 hover:border-gray-300 dark:hover:border-zinc-700 transition-all duration-150 shadow-sm flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300">
                Visits
              </span>
              <svg className="w-5 h-5 text-indigo-600 dark:text-indigo-400" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
              </svg>
            </div>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-3 tabular-nums">
              {data.pending_followups.length}
            </p>
          </div>
          <p className="text-xs text-gray-500 dark:text-zinc-400 mt-4 font-medium leading-snug">
            Upcoming follow-ups
          </p>
        </Link>

        {/* Vaccination gaps */}
        <Link
          href="/summary"
          className={`rounded-xl border p-5 transition-all duration-150 shadow-sm flex flex-col justify-between ${
            data.overdue_vaccine_count > 0
              ? 'border-amber-200 dark:border-amber-900/50 bg-amber-50/20 dark:bg-amber-950/10 hover:border-amber-300 dark:hover:border-amber-800'
              : 'border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 hover:border-gray-300 dark:hover:border-zinc-700'
          }`}
        >
          <div>
            <div className="flex items-center justify-between">
              <span
                className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${
                  data.overdue_vaccine_count > 0
                    ? 'bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300'
                    : 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300'
                }`}
              >
                {data.overdue_vaccine_count > 0 ? 'Action Needed' : 'Immunization'}
              </span>
              <svg
                className={`w-5 h-5 ${
                  data.overdue_vaccine_count > 0 ? 'text-amber-600 dark:text-amber-400' : 'text-emerald-600 dark:text-emerald-400'
                }`}
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="2"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.57-.598-3.75h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
                />
              </svg>
            </div>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-3 tabular-nums">
              {data.vaccination_gap_count}
            </p>
          </div>
          <p className="text-xs text-gray-500 dark:text-zinc-400 mt-4 font-medium leading-snug">
            {data.overdue_vaccine_count > 0
              ? `${data.overdue_vaccine_count} vaccine${data.overdue_vaccine_count > 1 ? 's' : ''} overdue`
              : 'Vaccination gaps'}
          </p>
        </Link>
      </div>

      {/* Main Section Grid: Activity and Follow-ups */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        {/* Recent Activity Feed */}
        <div className="md:col-span-2 rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6 shadow-sm">
          <h2 className="text-base font-semibold text-gray-900 dark:text-white mb-1">
            Recent Activity
          </h2>
          <p className="text-xs text-gray-500 dark:text-zinc-400 mb-6">
            Latest documents ingested and records extracted.
          </p>

          {data.recent_documents.length === 0 ? (
            <div className="text-center py-10 text-gray-400 dark:text-zinc-500 text-sm">
              No documents ingested yet. Use the upload button to add medical records.
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-zinc-800">
              {data.recent_documents.map((doc) => (
                <div key={doc.id} className="py-4 first:pt-0 last:pb-0 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-gray-50 dark:bg-zinc-800/60 text-gray-400 dark:text-zinc-500 rounded-lg">
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                      </svg>
                    </div>
                    <div>
                      <p className="font-semibold text-gray-800 dark:text-zinc-200 text-sm break-all">
                        {doc.file_name}
                      </p>
                      <p className="text-[11px] text-gray-400 dark:text-zinc-500 mt-0.5">
                        Ingested {new Date(doc.ingested_at.replace(/-/g, '/')).toLocaleDateString(undefined, {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </p>
                    </div>
                  </div>
                  <div className="sm:text-right">
                    <span className="inline-flex text-[11px] px-2.5 py-1 rounded-md font-medium bg-gray-50 dark:bg-zinc-800/40 text-gray-600 dark:text-zinc-400 border border-gray-100 dark:border-zinc-850">
                      {doc.what_was_found}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Upcoming Follow-ups List */}
        <div className="rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6 shadow-sm flex flex-col">
          <h2 className="text-base font-semibold text-gray-900 dark:text-white mb-1">
            Follow-ups
          </h2>
          <p className="text-xs text-gray-500 dark:text-zinc-400 mb-6">
            Action items from recent visits.
          </p>

          {data.pending_followups.length === 0 ? (
            <div className="text-center py-10 text-gray-400 dark:text-zinc-500 text-sm my-auto">
              No upcoming follow-ups scheduled.
            </div>
          ) : (
            <div className="space-y-4">
              {data.pending_followups.map((item, idx) => (
                <div
                  key={idx}
                  className="p-4 border border-gray-100 dark:border-zinc-800/80 bg-gray-50/40 dark:bg-zinc-900/40 rounded-lg"
                >
                  <div className="flex items-center justify-between text-[10px] font-semibold tracking-wider text-gray-400 dark:text-zinc-500 uppercase">
                    <span>{item.doctor || 'Unknown Doctor'}</span>
                    <span>{item.from_visit || '—'}</span>
                  </div>
                  <p className="text-xs text-gray-700 dark:text-zinc-300 mt-2 leading-relaxed border-l-2 border-indigo-500 pl-2">
                    {item.follow_up}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Links Section at the bottom */}
      <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-zinc-500 mb-4">
        All Sections
      </h2>
      <div className="grid sm:grid-cols-2 gap-3">
        {QUICK_LINKS.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="group flex flex-col rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 hover:border-gray-300 dark:hover:border-zinc-700 hover:shadow-sm transition-all duration-150"
          >
            <p className="font-semibold text-gray-900 dark:text-white text-sm">{link.label}</p>
            <p className="text-xs text-gray-500 dark:text-zinc-400 mt-1">{link.description}</p>
          </Link>
        ))}
      </div>
    </main>
  )
}
