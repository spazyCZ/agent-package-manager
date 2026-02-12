import { useParams } from 'react-router-dom';
import { useState, useEffect } from 'react';

interface PackageDetails {
  name: string;
  description: string;
  version: string;
  author: string;
  license: string;
  homepage: string;
  repository: string;
  downloads: number;
  readme: string;
  versions: string[];
  source: string;
  sourceCommit: string;
  artifactType: string;
}

function PackagePage() {
  const { name, version } = useParams<{ name: string; version?: string }>();
  const [pkg, setPkg] = useState<PackageDetails | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    // TODO: Implement actual API call
    setTimeout(() => {
      setPkg({
        name: name || 'unknown',
        description: 'An AI agent package for automating tasks',
        version: version || '1.0.0',
        author: 'aam-team',
        license: 'Apache-2.0',
        homepage: 'https://example.com',
        repository: 'https://github.com/example/repo',
        downloads: 12345,
        readme: `# ${name}\n\nA powerful AI agent package.\n\n## Installation\n\n\`\`\`bash\naam install ${name}\n\`\`\`\n\n## Usage\n\nImport and use the agent in your project.`,
        versions: ['1.0.0', '0.9.0', '0.8.0', '0.7.0'],
        source: 'google-gemini/gemini-skills',
        sourceCommit: 'e151a3b4c5d6',
        artifactType: 'agent',
      });
      setLoading(false);
    }, 500);
  }, [name, version]);

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-12 text-center">
        <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto"></div>
        <p className="mt-4 text-slate-600">Loading package...</p>
      </div>
    );
  }

  if (!pkg) {
    return (
      <div className="container mx-auto px-4 py-12 text-center">
        <h1 className="text-2xl font-bold text-slate-800">Package not found</h1>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="grid lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2">
          <h1 className="text-3xl font-bold mb-2">{pkg.name}</h1>
          <p className="text-slate-600 mb-6">{pkg.description}</p>

          {/* Install Command */}
          <div className="bg-slate-900 rounded-lg p-4 mb-8">
            <div className="flex justify-between items-center">
              <code className="text-green-400">aam install {pkg.name}</code>
              <button
                className="text-slate-400 hover:text-white"
                onClick={() => navigator.clipboard.writeText(`aam install ${pkg.name}`)}
              >
                Copy
              </button>
            </div>
          </div>

          {/* README */}
          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-xl font-semibold mb-4">README</h2>
            <div className="prose max-w-none">
              <pre className="whitespace-pre-wrap text-sm">{pkg.readme}</pre>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Package Info */}
          <div className="bg-white rounded-lg border p-6">
            <h3 className="font-semibold mb-4">Package Info</h3>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-slate-600">Version</dt>
                <dd className="font-medium">{pkg.version}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-600">License</dt>
                <dd className="font-medium">{pkg.license}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-600">Downloads</dt>
                <dd className="font-medium">{pkg.downloads.toLocaleString()}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-600">Author</dt>
                <dd className="font-medium">{pkg.author}</dd>
              </div>
              {pkg.source && (
                <div className="flex justify-between">
                  <dt className="text-slate-600">Source</dt>
                  <dd className="font-medium text-purple-600">{pkg.source}</dd>
                </div>
              )}
              {pkg.artifactType && (
                <div className="flex justify-between">
                  <dt className="text-slate-600">Type</dt>
                  <dd>
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                      {pkg.artifactType}
                    </span>
                  </dd>
                </div>
              )}
              {pkg.sourceCommit && (
                <div className="flex justify-between">
                  <dt className="text-slate-600">Commit</dt>
                  <dd className="font-mono text-xs">{pkg.sourceCommit}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Links */}
          <div className="bg-white rounded-lg border p-6">
            <h3 className="font-semibold mb-4">Links</h3>
            <div className="space-y-2 text-sm">
              {pkg.homepage && (
                <a
                  href={pkg.homepage}
                  className="block text-blue-600 hover:underline"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Homepage
                </a>
              )}
              {pkg.repository && (
                <a
                  href={pkg.repository}
                  className="block text-blue-600 hover:underline"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Repository
                </a>
              )}
            </div>
          </div>

          {/* Versions */}
          <div className="bg-white rounded-lg border p-6">
            <h3 className="font-semibold mb-4">Versions</h3>
            <div className="space-y-2 text-sm max-h-48 overflow-y-auto">
              {pkg.versions.map(v => (
                <a
                  key={v}
                  href={`/package/${pkg.name}/${v}`}
                  className={`block px-3 py-2 rounded ${
                    v === pkg.version
                      ? 'bg-blue-100 text-blue-700'
                      : 'hover:bg-slate-100'
                  }`}
                >
                  {v}
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PackagePage;
