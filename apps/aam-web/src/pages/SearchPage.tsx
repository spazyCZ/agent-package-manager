import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';

interface Package {
  name: string;
  description: string;
  version: string;
  downloads: number;
  author: string;
  source: string;
  artifactType: string;
}

function SearchPage() {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const [packages, setPackages] = useState<Package[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (query) {
      setLoading(true);
      // TODO: Implement actual API call
      setTimeout(() => {
        setPackages([
          {
            name: `${query}-agent`,
            description: `An AI agent for ${query} tasks`,
            version: '1.0.0',
            downloads: 1234,
            author: 'aam-team',
            source: 'aam-registry',
            artifactType: 'agent',
          },
          {
            name: `${query}-skill`,
            description: `A skill package for ${query}`,
            version: '0.5.0',
            downloads: 567,
            author: 'community',
            source: 'google-gemini/gemini-skills',
            artifactType: 'skill',
          },
        ]);
        setLoading(false);
      }, 500);
    }
  }, [query]);

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-2">
        {query ? `Search results for "${query}"` : 'Browse Packages'}
      </h1>
      <p className="text-slate-600 mb-8">
        {packages.length} packages found
      </p>

      {/* Filters */}
      <div className="flex gap-4 mb-8">
        <select className="px-4 py-2 border rounded-lg bg-white">
          <option>All Types</option>
          <option>Agents</option>
          <option>Skills</option>
          <option>Tools</option>
        </select>
        <select className="px-4 py-2 border rounded-lg bg-white">
          <option>Sort: Most Downloads</option>
          <option>Sort: Recently Updated</option>
          <option>Sort: Name</option>
        </select>
      </div>

      {/* Results */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto"></div>
          <p className="mt-4 text-slate-600">Loading...</p>
        </div>
      ) : (
        <div className="space-y-4">
          {packages.map((pkg) => (
            <Link
              key={pkg.name}
              to={`/package/${pkg.name}`}
              className="block bg-white rounded-lg border border-slate-200 p-6 hover:border-blue-500 hover:shadow-md transition-all"
            >
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-xl font-semibold text-blue-600">{pkg.name}</h2>
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                      {pkg.artifactType}
                    </span>
                  </div>
                  <p className="text-slate-600 mt-1">{pkg.description}</p>
                  <div className="flex items-center gap-4 mt-3 text-sm text-slate-500">
                    <span>v{pkg.version}</span>
                    <span>by {pkg.author}</span>
                    <span className="text-purple-600" title="Source">{pkg.source}</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-slate-600">{pkg.downloads.toLocaleString()} downloads</div>
                </div>
              </div>
            </Link>
          ))}

          {packages.length === 0 && !loading && (
            <div className="text-center py-12">
              <p className="text-slate-600">No packages found. Try a different search term.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default SearchPage;
