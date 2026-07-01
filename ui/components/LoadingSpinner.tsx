export default function LoadingSpinner({ label = 'Loading...' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-gray-400 dark:text-zinc-500">
      <span className="h-5 w-5 rounded-full border-2 border-gray-200 dark:border-zinc-700 border-t-gray-500 dark:border-t-zinc-400 animate-spin" />
      <span className="text-sm">{label}</span>
    </div>
  )
}
