const NotFoundPage = () => (
  <div className="min-h-screen flex items-center justify-center bg-slate-50">
    <div className="text-center max-w-md px-6">
      <p className="text-6xl font-bold text-slate-300 mb-4">404</p>
      <p className="text-slate-800 font-semibold text-lg">Page not found</p>
      <p className="text-sm text-slate-500 mt-2 mb-6">The page you're looking for doesn't exist or has been moved.</p>
      <a href="/" className="text-blue-600 hover:underline text-sm font-medium">Go to Dashboard</a>
    </div>
  </div>
);

export default NotFoundPage;
