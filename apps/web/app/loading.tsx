export default function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 border-4 border-primary-400 border-t-transparent rounded-full animate-spin" />
        <p className="text-gray-400">Chargement...</p>
      </div>
    </div>
  );
}
