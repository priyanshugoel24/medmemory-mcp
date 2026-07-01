'use client'

import { useCallback, useRef, useState } from 'react'
import { isAxiosError } from 'axios'
import { api } from '../../lib/api'

const ACCEPTED_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg']

type IngestResult = {
  success: boolean
  document_type: string | null
  medications_saved: number
  labs_saved: number
  diagnoses: string[]
  doctor_name: string | null
}

function isAccepted(file: File) {
  const name = file.name.toLowerCase()
  return ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext))
}

export default function UploadPage() {
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<IngestResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const upload = useCallback(async (file: File) => {
    if (!isAccepted(file)) {
      setError(`Unsupported file type. Please upload a PDF, PNG, or JPG.`)
      return
    }

    setError(null)
    setResult(null)
    setFileName(file.name)
    setUploading(true)
    setProgress(0)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await api.post('/ingest', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (event) => {
          if (event.total) {
            setProgress(Math.round((event.loaded / event.total) * 100))
          }
        },
      })
      setResult(response.data)
    } catch (err) {
      const detail = isAxiosError(err) ? err.response?.data?.detail : undefined
      setError(detail || 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      setDragActive(false)
      const file = e.dataTransfer.files?.[0]
      if (file) upload(file)
    },
    [upload]
  )

  const handleSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) upload(file)
    },
    [upload]
  )

  return (
    <main className="max-w-2xl mx-auto px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight mb-1 text-gray-900 dark:text-white">
        Upload a document
      </h1>
      <p className="text-gray-500 dark:text-zinc-400 mb-8">
        Add a prescription, lab report, or other health record. PDF, PNG, and JPG are supported.
      </p>

      <div
        onDragOver={(e) => {
          e.preventDefault()
          setDragActive(true)
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-14 text-center cursor-pointer transition-all duration-150 ${
          dragActive
            ? 'border-gray-900 dark:border-white bg-gray-50 dark:bg-zinc-800'
            : 'border-gray-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 hover:border-gray-300 dark:hover:border-zinc-600 hover:bg-gray-50 dark:hover:bg-zinc-800/50'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS.join(',')}
          onChange={handleSelect}
          className="hidden"
        />
        <p className="font-medium text-gray-900 dark:text-white">
          Drag and drop a file here, or click to browse
        </p>
        <p className="text-sm text-gray-400 dark:text-zinc-500 mt-1">PDF, PNG, JPG</p>
      </div>

      {uploading && (
        <div className="mt-6">
          <p className="text-sm text-gray-500 dark:text-zinc-400 mb-2">Uploading {fileName}...</p>
          <div className="h-1.5 bg-gray-100 dark:bg-zinc-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gray-900 dark:bg-white rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {error && (
        <div className="mt-6 border border-red-200 dark:border-red-800/50 bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-400 rounded-xl p-4 text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6 rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6 shadow-sm">
          <p className="font-semibold text-gray-900 dark:text-white mb-4">Extraction complete</p>
          <dl className="space-y-3 text-sm">
            {[
              { label: 'Document type', value: result.document_type ?? 'Unknown' },
              { label: 'Medications found', value: result.medications_saved },
              { label: 'Lab results found', value: result.labs_saved },
              { label: 'Doctor', value: result.doctor_name ?? 'Not detected' },
              {
                label: 'Diagnoses',
                value: result.diagnoses.length ? result.diagnoses.join(', ') : 'None detected',
              },
            ].map(({ label, value }) => (
              <div key={label} className="flex justify-between gap-4">
                <dt className="text-gray-400 dark:text-zinc-500 shrink-0">{label}</dt>
                <dd className="text-gray-900 dark:text-white text-right">{value}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </main>
  )
}
