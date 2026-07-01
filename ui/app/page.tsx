'use client'
import { useEffect, useState } from 'react'
import axios from 'axios'

const API = process.env.NEXT_PUBLIC_API_URL

export default function Home() {
const [medications, setMedications] = useState([])
const [loading, setLoading] = useState(true)

useEffect(() => {
axios.get(`${API}/medications`)
.then(r => setMedications(r.data.medications))
.finally(() => setLoading(false))
}, [])


return (
<main className="p-8 max-w-2xl mx-auto">
<h1 className="text-2xl font-semibold mb-6">MedMemory</h1>
<h2 className="text-lg font-medium mb-3">Current Medications</h2>
{loading ? (
<p className="text-gray-500">Loading...</p>
) : (
<ul className="space-y-2">
{medications.map((m: any, i: number) => (
<li key={i} className="border rounded p-3">
<span className="font-medium">{m.drug_name}</span> {m.dose} — {m.frequency}
</li>
))}
</ul>
)}
</main>
)
}