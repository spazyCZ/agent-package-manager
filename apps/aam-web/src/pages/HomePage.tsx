import { Link } from 'react-router-dom';

function HomePage() {
  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-slate-900 to-slate-800 text-white py-20">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-5xl font-bold mb-6">Agent Package Manager</h1>
          <p className="text-xl text-slate-300 mb-8 max-w-2xl mx-auto">
            The package registry for AI agents, skills, and tools. Discover, share, and manage agent
            packages with ease.
          </p>
          <div className="flex justify-center gap-4">
            <Link
              to="/search"
              className="bg-blue-600 hover:bg-blue-700 px-8 py-3 rounded-lg font-medium text-lg"
            >
              Browse Packages
            </Link>
            <a
              href="/docs"
              className="bg-slate-700 hover:bg-slate-600 px-8 py-3 rounded-lg font-medium text-lg"
            >
              Documentation
            </a>
          </div>
        </div>
      </section>

      {/* Quick Start */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">Quick Start</h2>
          <div className="max-w-2xl mx-auto">
            <div className="bg-slate-900 rounded-lg p-6 text-white font-mono">
              <div className="text-slate-400 mb-2"># Install a package</div>
              <div className="text-green-400 mb-4">$ aam install my-agent</div>

              <div className="text-slate-400 mb-2"># Search for packages</div>
              <div className="text-green-400 mb-4">$ aam search chatbot</div>

              <div className="text-slate-400 mb-2"># Publish your package</div>
              <div className="text-green-400">$ aam publish</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">Features</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
                📦
              </div>
              <h3 className="text-xl font-semibold mb-2">Easy Publishing</h3>
              <p className="text-slate-600">
                Publish your agents, skills, and tools with a single command. Share with the
                community.
              </p>
            </div>
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
                🔍
              </div>
              <h3 className="text-xl font-semibold mb-2">Discover & Search</h3>
              <p className="text-slate-600">
                Find the perfect package for your needs with powerful search and filtering.
              </p>
            </div>
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
                🔐
              </div>
              <h3 className="text-xl font-semibold mb-2">Secure & Verified</h3>
              <p className="text-slate-600">
                All packages are verified and signed. Trust the code you install.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold text-blue-600">1,000+</div>
              <div className="text-slate-600">Packages</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-blue-600">500+</div>
              <div className="text-slate-600">Publishers</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-blue-600">50K+</div>
              <div className="text-slate-600">Downloads</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-blue-600">100%</div>
              <div className="text-slate-600">Open Source</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default HomePage;
