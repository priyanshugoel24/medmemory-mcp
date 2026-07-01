'use client'

import { useEffect, useState } from 'react'
import { api } from '../../lib/api'
import LoadingSpinner from '../../components/LoadingSpinner'
import EmptyState from '../../components/EmptyState'

type Medication = {
  drug_name: string
  dose: string | null
  frequency: string | null
  condition_treated: string | null
  prescriber: string | null
  start_date: string | null
}

export default function MedicationsPage() {
  const [medications, setMedications] = useState<Medication[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get('/medications')
      .then((r) => setMedications(r.data.medications))
      .finally(() => setLoading(false))
  }, [])

  return (
    <main className="max-w-5xl mx-auto px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight mb-1 text-gray-900 dark:text-white">
        Medications
      </h1>
      <p className="text-gray-500 dark:text-zinc-400 mb-8">
        Everything currently active on your record.
      </p>

      {loading ? (
        <LoadingSpinner />
      ) : medications.length === 0 ? (
        <EmptyState
          title="No active medications"
          description="Upload a prescription to start tracking medications."
        />
      ) : (
        <div className="rounded-xl border border-gray-200 dark:border-zinc-800 overflow-hidden bg-white dark:bg-zinc-900 shadow-sm">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-zinc-800/60 border-b border-gray-200 dark:border-zinc-700">
              <tr className="text-left text-gray-500 dark:text-zinc-400">
                <th className="px-4 py-3 font-medium">Drug</th>
                <th className="px-4 py-3 font-medium">Dose</th>
                <th className="px-4 py-3 font-medium">Frequency</th>
                <th className="px-4 py-3 font-medium">Condition treated</th>
                <th className="px-4 py-3 font-medium">Start date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-zinc-800">
              {medications.map((m, i) => (
                <tr key={i} className="hover:bg-gray-50 dark:hover:bg-zinc-800/40 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{m.drug_name}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-zinc-300">{m.dose ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-zinc-300">{m.frequency ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-zinc-300">{m.condition_treated ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-zinc-300">{m.start_date ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  )
}
