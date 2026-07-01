'use client'

import { useEffect, useState } from 'react'
import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { api } from '../../lib/api'
import LoadingSpinner from '../../components/LoadingSpinner'
import EmptyState from '../../components/EmptyState'

type Reading = {
  marker_name: string
  value: number
  unit: string | null
  reference_min: number | null
  reference_max: number | null
  test_date: string
  lab_name: string | null
}

type ChartPoint = {
  test_date: string
  value: number
  range?: [number, number]
}

export default function LabsPage() {
  const [markers, setMarkers] = useState<string[]>([])
  const [selected, setSelected] = useState<string>('')
  const [readings, setReadings] = useState<Reading[]>([])
  const [loadingMarkers, setLoadingMarkers] = useState(true)
  const [loadingTrend, setLoadingTrend] = useState(false)

  useEffect(() => {
    api
      .get('/lab-markers')
      .then((r) => {
        setMarkers(r.data.markers)
        if (r.data.markers.length) setSelected(r.data.markers[0])
      })
      .finally(() => setLoadingMarkers(false))
  }, [])

  useEffect(() => {
    if (!selected) return
    let cancelled = false
    async function fetchTrend() {
      setLoadingTrend(true)
      try {
        const r = await api.get(`/lab-trend/${encodeURIComponent(selected)}`)
        if (!cancelled) setReadings(r.data.readings)
      } finally {
        if (!cancelled) setLoadingTrend(false)
      }
    }
    fetchTrend()
    return () => {
      cancelled = true
    }
  }, [selected])

  const chartData: ChartPoint[] = readings.map((r) => ({
    test_date: r.test_date,
    value: r.value,
    range:
      r.reference_min != null && r.reference_max != null
        ? [r.reference_min, r.reference_max]
        : undefined,
  }))

  return (
    <main className="max-w-5xl mx-auto px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight mb-1 text-gray-900 dark:text-white">
        Lab results
      </h1>
      <p className="text-gray-500 dark:text-zinc-400 mb-8">
        Track a marker&apos;s trend over time.
      </p>

      {loadingMarkers ? (
        <LoadingSpinner />
      ) : markers.length === 0 ? (
        <EmptyState
          title="No lab results yet"
          description="Upload a lab report to start tracking markers."
        />
      ) : (
        <>
          <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-zinc-500 mb-2">
            Marker
          </label>
          <select
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            className="border border-gray-200 dark:border-zinc-700 rounded-lg px-3 py-2 mb-8 bg-white dark:bg-zinc-900 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 dark:focus:ring-zinc-600 transition-colors"
          >
            {markers.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>

          {loadingTrend ? (
            <LoadingSpinner />
          ) : readings.length === 0 ? (
            <EmptyState title="No readings for this marker" />
          ) : (
            <>
              <div className="rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6 mb-6 shadow-sm">
                <ResponsiveContainer width="100%" height={320}>
                  <ComposedChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-gray-100 dark:text-zinc-800" />
                    <XAxis dataKey="test_date" tick={{ fontSize: 11, fill: 'currentColor' }} className="text-gray-400 dark:text-zinc-500" />
                    <YAxis tick={{ fontSize: 11, fill: 'currentColor' }} className="text-gray-400 dark:text-zinc-500" />
                    <Tooltip
                      contentStyle={{
                        background: 'var(--tooltip-bg, white)',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        fontSize: '12px',
                      }}
                    />
                    <Area
                      dataKey="range"
                      stroke="none"
                      fill="#22c55e"
                      fillOpacity={0.12}
                      name="Reference range"
                      connectNulls
                    />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#6366f1"
                      strokeWidth={2}
                      dot={{ r: 3, fill: '#6366f1' }}
                      name={selected}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>

              <div className="rounded-xl border border-gray-200 dark:border-zinc-800 overflow-hidden bg-white dark:bg-zinc-900 shadow-sm">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-zinc-800/60 border-b border-gray-200 dark:border-zinc-700">
                    <tr className="text-left text-gray-500 dark:text-zinc-400">
                      <th className="px-4 py-3 font-medium">Date</th>
                      <th className="px-4 py-3 font-medium">Value</th>
                      <th className="px-4 py-3 font-medium">Unit</th>
                      <th className="px-4 py-3 font-medium">Reference range</th>
                      <th className="px-4 py-3 font-medium">Lab</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-zinc-800">
                    {readings.map((r, i) => (
                      <tr key={i} className="hover:bg-gray-50 dark:hover:bg-zinc-800/40 transition-colors">
                        <td className="px-4 py-3 text-gray-600 dark:text-zinc-300">{r.test_date}</td>
                        <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{r.value}</td>
                        <td className="px-4 py-3 text-gray-600 dark:text-zinc-300">{r.unit ?? '—'}</td>
                        <td className="px-4 py-3 text-gray-600 dark:text-zinc-300">
                          {r.reference_min != null && r.reference_max != null
                            ? `${r.reference_min} – ${r.reference_max}`
                            : '—'}
                        </td>
                        <td className="px-4 py-3 text-gray-600 dark:text-zinc-300">{r.lab_name ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </>
      )}
    </main>
  )
}
