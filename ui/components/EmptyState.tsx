export default function EmptyState({
  title,
  description,
}: {
  title: string
  description?: string
}) {
  return (
    <div className="text-center py-16 border border-dashed border-gray-200 dark:border-zinc-700 rounded-xl">
      <p className="text-gray-700 dark:text-gray-300 font-medium">{title}</p>
      {description && <p className="text-gray-400 dark:text-zinc-500 text-sm mt-1">{description}</p>}
    </div>
  )
}
