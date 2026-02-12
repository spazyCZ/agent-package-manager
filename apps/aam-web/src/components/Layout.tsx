import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';

function Layout() {
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-slate-900 text-white">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="text-2xl font-bold text-blue-400 hover:text-blue-300">
              AAM
            </Link>

            <form onSubmit={handleSearch} className="flex-1 max-w-xl mx-8">
              <input
                type="search"
                placeholder="Search packages..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full px-4 py-2 rounded-lg bg-slate-800 text-white placeholder-slate-400 border border-slate-700 focus:border-blue-500 focus:outline-none"
              />
            </form>

            <nav className="flex items-center gap-4">
              <Link to="/search" className="text-slate-300 hover:text-white">
                Browse
              </Link>
            </nav>
          </div>
        </div>
      </header>

      <main className="flex-1 bg-slate-50">
        <Outlet />
      </main>

      <footer className="bg-slate-900 text-slate-400 py-8">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div>
              <span className="text-blue-400 font-bold">AAM</span> - Agent Package Manager
            </div>
            <div className="flex gap-6">
              <a href="https://storage.googleapis.com/aam-docs-test/index.html" className="hover:text-white" target="_blank" rel="noopener noreferrer">
                Documentation
              </a>

              <a
                href="https://github.com/spazyCZ/agent-package-manager"
                className="hover:text-white"
                target="_blank"
                rel="noopener noreferrer"
              >
                GitHub
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Layout;
