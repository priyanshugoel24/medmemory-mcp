'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { api } from '../lib/api'
import LoadingSpinner from '../components/LoadingSpinner'

type Stats = {
  medicationCount: number
  markerCount: number
  followUpCount: number
  vaccinationGapCount: number
}

const QUICK_LINKS = [
  { href: '/upload', label: 'Upload a document', description: 'Add a prescription, lab report, or record' },
  { href: '/medications', label: 'View medications', description: 'See everything you are currently taking' },
  { href: '/labs', label: 'Explore lab trends', description: 'Track a marker over time' },
  { href: '/summary', label: 'Health summary', description: 'A printable overview for your doctor' },
]

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/medications'),
      api.get('/lab-markers'),
      api.get('/summary'),
      api.get('/vaccination-status'),
    ])
      .then(([medications, markers, summary, vaccinationStatus]) => {
        setStats({
          medicationCount: medications.data.medications.length,
          markerCount: markers.data.markers.length,
          followUpCount: summary.data.pending_follow_ups.length,
          vaccinationGapCount:
            vaccinationStatus.data.overdue.length + vaccinationStatus.data.missing.length,
        })
      })
      .finally(() => setLoading(false))
  }, [])

  const cards = [
    { label: 'Active medications', value: stats?.medicationCount },
    { label: 'Lab markers on record', value: stats?.markerCount },
    { label: 'Upcoming follow-ups', value: stats?.followUpCount },
    { label: 'Vaccination gaps', value: stats?.vaccinationGapCount },
  ]

  return (
    <main className="max-w-5xl mx-auto px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight mb-1 text-gray-900 dark:text-white">
        Welcome back
      </h1>
      <p className="text-gray-500 dark:text-zinc-400 mb-10">
        Here&apos;s a snapshot of your health record.
      </p>

      {loading ? (
        <LoadingSpinner />
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
          {cards.map((card) => (
            <div
              key={card.label}
              className="rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 shadow-sm"
            >
              <p className="text-3xl font-bold text-gray-900 dark:text-white tabular-nums">
                {card.value ?? '—'}
              </p>
              <p className="text-xs text-gray-500 dark:text-zinc-400 mt-2 leading-snug">
                {card.label}
              </p>
            </div>
          ))}
        </div>
      )}

      <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400 dark:text-zinc-500 mb-4">
        Quick links
      </h2>
      <div className="grid sm:grid-cols-2 gap-3">
        {QUICK_LINKS.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="group flex flex-col rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 hover:border-gray-300 dark:hover:border-zinc-600 hover:shadow-md transition-all duration-150"
          >
            <p className="font-medium text-gray-900 dark:text-white text-sm">{link.label}</p>
            <p className="text-xs text-gray-500 dark:text-zinc-400 mt-1">{link.description}</p>
          </Link>
        ))}
      </div>
    </main>
  )
}
