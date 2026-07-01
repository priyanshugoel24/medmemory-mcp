'use client'

import { useEffect, useState } from 'react'
import { api } from '../../lib/api'
import LoadingSpinner from '../../components/LoadingSpinner'

type Medication = {
  drug_name: string
  dose: string | null
  frequency: string | null
  condition_treated: string | null
  start_date: string | null
}

type LabReading = {
  marker_name: string
  value: number
  unit: string | null
  test_date: string
}

type Visit = {
  visit_date: string | null
  speciality: string | null
  doctor_name: string | null
  diagnosis: string | null
  follow_up: string | null
}

type Vaccination = {
  vaccine_name: string
  date_administered: string | null
  dose_number: number
  provider: string | null
}

type Allergy = {
  allergen: string
  reaction: string | null
  severity: string | null
  noted_date: string | null
}

type FollowUp = {
  from_visit: string | null
  doctor: string | null
  follow_up: string
}

type Summary = {
  generated_on: string
  active_medications: Medication[]
  known_allergies: Allergy[]
  recent_lab_results: Record<string, LabReading>
  recent_visits_by_specialty: Visit[]
  vaccinations_on_record: Vaccination[]
  pending_follow_ups: FollowUp[]
  disclaimer: string
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-8 break-inside-avoid">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400 dark:text-zinc-500 border-b border-gray-100 dark:border-zinc-800 pb-2 mb-4">
        {title}
      </h2>
      {children}
    </section>
  )
}

export default function SummaryPage() {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get('/summary')
      .then((r) => setSummary(r.data))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <main className="max-w-3xl mx-auto px-6 py-10">
        <LoadingSpinner />
      </main>
    )
  }

  if (!summary) return null

  const labEntries = Object.entries(summary.recent_lab_results)

  return (
    <main className="max-w-3xl mx-auto px-6 py-10 print:py-0">
      <div className="flex items-start justify-between mb-10 print:hidden">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight mb-1 text-gray-900 dark:text-white">
            Health summary
          </h1>
          <p className="text-gray-500 dark:text-zinc-400 text-sm">Generated on {summary.generated_on}</p>
        </div>
        <button
          onClick={() => window.print()}
          className="px-4 py-2 bg-gray-900 dark:bg-white text-white dark:text-gray-900 text-sm font-medium rounded-lg hover:bg-gray-700 dark:hover:bg-gray-100 transition-colors"
        >
          Print
        </button>
      </div>

      <div className="hidden print:block mb-8">
        <h1 className="text-2xl font-semibold">Health summary</h1>
        <p className="text-gray-500 text-sm">Generated on {summary.generated_on}</p>
      </div>

      <Section title="Active medications">
        {summary.active_medications.length === 0 ? (
          <p className="text-gray-400 dark:text-zinc-500 text-sm">No active medications on record.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {summary.active_medications.map((m, i) => (
              <li key={i} className="text-gray-700 dark:text-zinc-300">
                <span className="font-medium text-gray-900 dark:text-white">{m.drug_name}</span>
                {m.dose && ` — ${m.dose}`}
                {m.frequency && ` — ${m.frequency}`}
                {m.condition_treated && ` (for ${m.condition_treated})`}
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Recent lab results">
        {labEntries.length === 0 ? (
          <p className="text-gray-400 dark:text-zinc-500 text-sm">No lab results on record.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {labEntries.map(([marker, reading]) => (
              <li key={marker} className="text-gray-700 dark:text-zinc-300">
                <span className="font-medium text-gray-900 dark:text-white">{marker}</span>: {reading.value}{' '}
                {reading.unit ?? ''}{' '}
                <span className="text-gray-400 dark:text-zinc-500">({reading.test_date})</span>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Recent visits">
        {summary.recent_visits_by_specialty.length === 0 ? (
          <p className="text-gray-400 dark:text-zinc-500 text-sm">No visits on record.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {summary.recent_visits_by_specialty.map((v, i) => (
              <li key={i} className="text-gray-700 dark:text-zinc-300">
                <span className="font-medium text-gray-900 dark:text-white">{v.speciality ?? 'General'}</span>
                {v.doctor_name && ` — ${v.doctor_name}`}
                {v.visit_date && ` (${v.visit_date})`}
                {v.diagnosis && `: ${v.diagnosis}`}
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Vaccinations on record">
        {summary.vaccinations_on_record.length === 0 ? (
          <p className="text-gray-400 dark:text-zinc-500 text-sm">No vaccinations on record.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {summary.vaccinations_on_record.map((v, i) => (
              <li key={i} className="text-gray-700 dark:text-zinc-300">
                <span className="font-medium text-gray-900 dark:text-white">{v.vaccine_name}</span>
                {v.date_administered && ` — ${v.date_administered}`}
                {v.dose_number > 1 && ` (dose ${v.dose_number})`}
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Known allergies">
        {summary.known_allergies.length === 0 ? (
          <p className="text-gray-400 dark:text-zinc-500 text-sm">No known allergies on record.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {summary.known_allergies.map((a, i) => (
              <li key={i} className="text-gray-700 dark:text-zinc-300">
                <span className="font-medium text-gray-900 dark:text-white">{a.allergen}</span>
                {a.reaction && ` — ${a.reaction}`}
                {a.severity && ` (${a.severity})`}
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Pending follow-ups">
        {summary.pending_follow_ups.length === 0 ? (
          <p className="text-gray-400 dark:text-zinc-500 text-sm">No pending follow-ups.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {summary.pending_follow_ups.map((f, i) => (
              <li key={i} className="text-gray-700 dark:text-zinc-300">
                {f.follow_up}
                {f.doctor && ` — ${f.doctor}`}
                {f.from_visit && ` (from visit on ${f.from_visit})`}
              </li>
            ))}
          </ul>
        )}
      </Section>

      <p className="text-xs text-gray-300 dark:text-zinc-600 border-t border-gray-100 dark:border-zinc-800 pt-4 mt-10">
        {summary.disclaimer}
      </p>
    </main>
  )
}
