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
              href="https://storage.googleapis.com/aam-docs-test/index.html"
              className="bg-slate-700 hover:bg-slate-600 px-8 py-3 rounded-lg font-medium text-lg"
              target="_blank"
              rel="noopener noreferrer"
            >
              Documentation
            </a>
          </div>
        </div>
      </section>

      {/* Quick Start */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-4">Quick Start</h2>
          <p className="text-center text-slate-500 mb-12 max-w-2xl mx-auto">
            Use AAM from the terminal or let your AI agent manage packages through the built-in MCP server.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 max-w-5xl mx-auto">
            {/* CLI Column */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-green-100 text-green-600 font-bold text-sm">
                  &gt;_
                </span>
                <span className="font-semibold text-slate-800">CLI</span>
                <span className="text-slate-400 text-sm">— run from your terminal</span>
              </div>
              <div className="bg-slate-900 rounded-lg p-6 text-white font-mono h-full">
                <div className="text-slate-400 mb-2"># 1. Add a source repository</div>
                <div className="text-green-400 mb-4">$ aam source add openai/skills</div>

                <div className="text-slate-400 mb-2"># 2. List available packages</div>
                <div className="text-green-400 mb-4">$ aam source list openai/skills</div>

                <div className="text-slate-400 mb-2"># 3. Install the skill you need</div>
                <div className="text-green-400">$ aam install spreadsheet</div>
              </div>
            </div>
            {/* MCP Column */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-violet-100 text-violet-600 font-bold text-sm">
                  AI
                </span>
                <span className="font-semibold text-slate-800">MCP Server</span>
                <span className="text-slate-400 text-sm">— built into the CLI</span>
              </div>
              <div className="bg-slate-900 rounded-lg p-6 text-white font-mono h-full">
                <div className="text-slate-400 mb-2"># Start the MCP server for your IDE</div>
                <div className="text-violet-400 mb-4">$ aam mcp serve</div>

                <div className="text-slate-400 mb-2"># Then ask your AI agent:</div>
                <div className="text-slate-300 italic">"Add the openai/skills source,</div>
                <div className="text-slate-300 italic">&nbsp;show me what's available,</div>
                <div className="text-slate-300 italic">&nbsp;and install the spreadsheet skill"</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases by Persona */}
      <section className="py-24 bg-gradient-to-b from-slate-900 to-slate-800 text-white relative overflow-hidden">
        <div className="container mx-auto px-4 relative z-10">
          {/* Section Header */}
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">
              Built for Every Role in the AI Stack
            </h2>
            <p className="text-xl text-slate-300 max-w-3xl mx-auto leading-relaxed">
              Whether you build skills, consume them, lead a team, or curate complete agent
              stacks — AAM fits your workflow.
            </p>
          </div>

          {/* 2x2 Persona Grid */}
          <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">

            {/* Card 1: For Developers */}
            <div className="bg-slate-800\/50 border border-emerald-500\/30 rounded-lg p-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="inline-flex items-center gap-2 bg-emerald-900\/40 border border-emerald-500\/30 rounded-full px-4 py-1">
                  <span className="text-emerald-400 font-semibold text-xs uppercase tracking-wide">Developer</span>
                </div>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Package and Publish Your Skills</h3>
              <p className="text-slate-300 text-sm mb-4 leading-relaxed">
                Create, version, and share AI skills from your codebase. Treat agent artifacts
                like any other software dependency.
              </p>
              <ul className="text-slate-300 text-sm space-y-2 mb-5">
                <li className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5">&#10003;</span>
                  <span>Scaffold packages from existing code with <code className="text-emerald-400 font-mono text-xs">aam pkg create</code></span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5">&#10003;</span>
                  <span>Semver versioning and automatic dependency resolution</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5">&#10003;</span>
                  <span>Publish to local or remote registries with <code className="text-emerald-400 font-mono text-xs">aam pkg publish</code></span>
                </li>
              </ul>
              <div className="bg-slate-950 rounded p-4 font-mono text-sm space-y-2">
                <div className="text-slate-500"># Package your skill and publish</div>
                <div className="text-emerald-400">$ aam pkg create my-code-review</div>
                <div className="text-emerald-400">$ aam pkg publish</div>
              </div>
            </div>

            {/* Card 2: For Teams */}
            <div className="bg-slate-800\/50 border border-blue-500\/30 rounded-lg p-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="inline-flex items-center gap-2 bg-blue-900\/40 border border-blue-500\/30 rounded-full px-4 py-1">
                  <span className="text-blue-400 font-semibold text-xs uppercase tracking-wide">Team</span>
                </div>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Standardize Skills Across Your Organization</h3>
              <p className="text-slate-300 text-sm mb-4 leading-relaxed">
                Private registries, shared configs, and consistent tooling so every team member
                uses the same vetted skills.
              </p>
              <ul className="text-slate-300 text-sm space-y-2 mb-5">
                <li className="flex items-start gap-2">
                  <span className="text-blue-400 mt-0.5">&#10003;</span>
                  <span>Host a private team registry with <code className="text-blue-400 font-mono text-xs">aam registry init</code></span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-400 mt-0.5">&#10003;</span>
                  <span>Shared <code className="text-blue-400 font-mono text-xs">aam-config.yaml</code> for team-wide defaults and policies</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-400 mt-0.5">&#10003;</span>
                  <span>Package signing and security policies for trusted deployments</span>
                </li>
              </ul>
              <div className="bg-slate-950 rounded p-4 font-mono text-sm space-y-2">
                <div className="text-slate-500"># Set up a private team registry</div>
                <div className="text-blue-400">$ aam registry init ~/team-registry</div>
                <div className="text-blue-400">$ aam pkg publish --registry file:///team-registry</div>
              </div>
            </div>

            {/* Card 3: For Skills Users */}
            <div className="bg-slate-800\/50 border border-violet-500\/30 rounded-lg p-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="inline-flex items-center gap-2 bg-violet-900\/40 border border-violet-500\/30 rounded-full px-4 py-1">
                  <span className="text-violet-400 font-semibold text-xs uppercase tracking-wide">Skills User</span>
                </div>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Discover and Install Ready-Made Skills</h3>
              <p className="text-slate-300 text-sm mb-4 leading-relaxed">
                One command to find, install, and deploy community skills. The same skill works
                across Cursor, Claude, Copilot, and Codex.
              </p>
              <ul className="text-slate-300 text-sm space-y-2 mb-5">
                <li className="flex items-start gap-2">
                  <span className="text-violet-400 mt-0.5">&#10003;</span>
                  <span>Search and install instantly with <code className="text-violet-400 font-mono text-xs">aam search</code> and <code className="text-violet-400 font-mono text-xs">aam install</code></span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-violet-400 mt-0.5">&#10003;</span>
                  <span>Multi-platform deploy — same package works on every AI platform</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-violet-400 mt-0.5">&#10003;</span>
                  <span>Browse and explore packages from the web registry</span>
                </li>
              </ul>
              <div className="bg-slate-950 rounded p-4 font-mono text-sm space-y-2">
                <div className="text-slate-500"># Find and install a community skill</div>
                <div className="text-violet-400">$ aam search code-review</div>
                <div className="text-violet-400">$ aam install @anthropic/code-review</div>
              </div>
            </div>

            {/* Card 4: For AI Practitioners */}
            <div className="bg-slate-800\/50 border border-amber-500\/30 rounded-lg p-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="inline-flex items-center gap-2 bg-amber-900\/40 border border-amber-500\/30 rounded-full px-4 py-1">
                  <span className="text-amber-400 font-semibold text-xs uppercase tracking-wide">AI Practitioner</span>
                </div>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Curate Complete Agent Bundles</h3>
              <p className="text-slate-300 text-sm mb-4 leading-relaxed">
                Combine skills, prompts, agents, and instructions into deployable packages.
                Ship entire agent stacks to any supported platform.
              </p>
              <ul className="text-slate-300 text-sm space-y-2 mb-5">
                <li className="flex items-start gap-2">
                  <span className="text-amber-400 mt-0.5">&#10003;</span>
                  <span>Bundle skills + prompts + agent configs into one package</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-amber-400 mt-0.5">&#10003;</span>
                  <span>Dependency resolution — agent packages that reference skill packages</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-amber-400 mt-0.5">&#10003;</span>
                  <span>Deploy complete agent stacks to Cursor, Claude, Copilot, or Codex</span>
                </li>
              </ul>
              <div className="bg-slate-950 rounded p-4 font-mono text-sm space-y-2">
                <div className="text-slate-500"># Install a full agent bundle with dependencies</div>
                <div className="text-amber-400">$ aam install @team/security-audit-agent</div>
                <div className="text-slate-400 text-xs mt-1">Resolves: 3 skills, 2 prompts, 1 agent config</div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* Use Case: Git Source Management */}
      <section className="py-24 bg-gradient-to-b from-slate-900 to-slate-800 text-white relative overflow-hidden">
        <div className="container mx-auto px-4 relative z-10">
          {/* Section Header */}
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 bg-slate-800\/80 border border-slate-700\/50 rounded-full px-5 py-2 mb-6">
              <span className="text-emerald-400 font-semibold text-sm uppercase tracking-wide">
                Use Case
              </span>
              <span className="text-slate-500">|</span>
              <span className="text-slate-300 text-sm">npm-style workflow for AI skills</span>
            </div>
            <h2 className="text-4xl font-bold mb-4">
              Manage 3rd-Party AI Skills Like Dependencies
            </h2>
            <p className="text-xl text-slate-300 max-w-4xl mx-auto leading-relaxed">
              Track skills from Anthropic, OpenAI, GitHub, and other providers as git sources.
              Observe upstream changes, install curated artifacts, and keep everything in sync
              — just like <code className="text-emerald-400 font-mono">npm</code> or{' '}
              <code className="text-emerald-400 font-mono">pip</code>, but for agentic artifacts.
            </p>
          </div>

          {/* Three-Step Workflow */}
          <div className="grid lg:grid-cols-3 gap-8 mb-16">
            {/* Step 1: Add Sources */}
            <div className="bg-slate-800\/50 border border-emerald-500\/30 rounded-lg p-6">
              <div className="flex items-center gap-3 mb-4">
                <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-emerald-100 text-emerald-600 font-bold text-sm">
                  1
                </span>
                <h3 className="text-lg font-semibold text-emerald-400">Add Git Sources</h3>
              </div>
              <p className="text-slate-300 text-sm mb-4 leading-relaxed">
                Register any public or private git repository as a tracked source. AAM clones it,
                scans for skills, agents, and prompts, and indexes everything locally.
              </p>
              <div className="bg-slate-950 rounded p-4 font-mono text-sm space-y-3">
                <div>
                  <div className="text-slate-500"># Anthropic's official Claude skills</div>
                  <div className="text-emerald-400">$ aam source add anthropic/claude-skills</div>
                </div>
                <div>
                  <div className="text-slate-500"># OpenAI curated Codex skills</div>
                  <div className="text-emerald-400">$ aam source add openai/skills --path skills/.curated</div>
                </div>
                <div>
                  <div className="text-slate-500"># GitHub Copilot community skills</div>
                  <div className="text-emerald-400">$ aam source add github/awesome-copilot</div>
                </div>
              </div>
            </div>

            {/* Step 2: Observe Changes */}
            <div className="bg-slate-800\/50 border border-blue-500\/30 rounded-lg p-6">
              <div className="flex items-center gap-3 mb-4">
                <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-bold text-sm">
                  2
                </span>
                <h3 className="text-lg font-semibold text-blue-400">Observe Changes</h3>
              </div>
              <p className="text-slate-300 text-sm mb-4 leading-relaxed">
                Fetch upstream changes and see exactly what's new, modified, or removed. Never
                miss an update to the skills you depend on — stay informed before upgrading.
              </p>
              <div className="bg-slate-950 rounded p-4 font-mono text-sm space-y-3">
                <div>
                  <div className="text-slate-500"># Check all sources for updates</div>
                  <div className="text-blue-400">$ aam source update --all</div>
                </div>
                <div className="border-l-2 border-l-emerald-400 pl-4 ml-4 space-y-2">
                  <div className="text-slate-300">anthropic/claude-skills</div>
                  <div className="text-emerald-400">  + 3 new skills</div>
                  <div className="text-amber-400">  ~ 1 modified</div>
                  <div className="text-slate-500">  = 12 unchanged</div>
                </div>
                <div className="border-l-2 border-l-blue-400 pl-4 ml-4 space-y-2">
                  <div className="text-slate-300">openai/skills:.curated</div>
                  <div className="text-emerald-400">  + 1 new skill</div>
                  <div className="text-red-400">  - 1 removed</div>
                  <div className="text-slate-500">  = 8 unchanged</div>
                </div>
              </div>
            </div>

            {/* Step 3: Install & Verify */}
            <div className="bg-slate-800\/50 border border-amber-500\/30 rounded-lg p-6">
              <div className="flex items-center gap-3 mb-4">
                <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-amber-100 text-amber-600 font-bold text-sm">
                  3
                </span>
                <h3 className="text-lg font-semibold text-amber-400">Install & Verify</h3>
              </div>
              <p className="text-slate-300 text-sm mb-4 leading-relaxed">
                Package and install the skills you need. AAM tracks checksums so you can always
                verify integrity and see local modifications before upgrading.
              </p>
              <div className="bg-slate-950 rounded p-4 font-mono text-sm space-y-3">
                <div>
                  <div className="text-slate-500"># Create a package from a source</div>
                  <div className="text-amber-400">$ aam pkg create \</div>
                  <div className="text-amber-400">    --from-source anthropic/claude-skills \</div>
                  <div className="text-amber-400">    --artifacts code-review,refactor-py</div>
                </div>
                <div>
                  <div className="text-slate-500"># Verify installed skills are unmodified</div>
                  <div className="text-amber-400">$ aam verify --all</div>
                </div>
                <div className="border-l-2 border-l-amber-400 pl-4 ml-4 space-y-2">
                  <div className="text-emerald-400">  code-review: OK (3 files)</div>
                  <div className="text-amber-400">  refactor-py: MODIFIED (1 file)</div>
                </div>
              </div>
            </div>
          </div>

          {/* Supported Providers */}
          <div className="text-center">
            <p className="text-slate-400 text-sm uppercase tracking-wide mb-6 font-semibold">
              Works with skills from any git-hosted provider
            </p>
            <div className="flex justify-center items-center gap-12 flex-col md:flex-row">
              <div className="flex flex-col items-center gap-2">
                <div className="w-16 h-16 bg-slate-800\/80 rounded-lg flex items-center justify-center border border-slate-700\/50">
                  <span className="text-3xl">🤖</span>
                </div>
                <span className="text-slate-300 text-sm font-medium">OpenAI</span>
                <span className="text-slate-500 text-xs font-mono">openai/skills</span>
              </div>
              <div className="flex flex-col items-center gap-2">
                <div className="w-16 h-16 bg-slate-800\/80 rounded-lg flex items-center justify-center border border-slate-700\/50">
                  <span className="text-3xl">🧠</span>
                </div>
                <span className="text-slate-300 text-sm font-medium">Anthropic</span>
                <span className="text-slate-500 text-xs font-mono">anthropic/claude-skills</span>
              </div>
              <div className="flex flex-col items-center gap-2">
                <div className="w-16 h-16 bg-slate-800\/80 rounded-lg flex items-center justify-center border border-slate-700\/50">
                  <span className="text-3xl">🐙</span>
                </div>
                <span className="text-slate-300 text-sm font-medium">GitHub Copilot</span>
                <span className="text-slate-500 text-xs font-mono">github/awesome-copilot</span>
              </div>
              <div className="flex flex-col items-center gap-2">
                <div className="w-16 h-16 bg-slate-800\/80 rounded-lg flex items-center justify-center border border-slate-700\/50">
                  <span className="text-3xl">🦊</span>
                </div>
                <span className="text-slate-300 text-sm font-medium">GitLab</span>
                <span className="text-slate-500 text-xs font-mono">team/custom-skills</span>
              </div>
              <div className="flex flex-col items-center gap-2">
                <div className="w-16 h-16 bg-slate-800\/80 rounded-lg flex items-center justify-center border border-slate-700\/50">
                  <span className="text-3xl">🔧</span>
                </div>
                <span className="text-slate-300 text-sm font-medium">Any Git Repo</span>
                <span className="text-slate-500 text-xs font-mono">your-org/skills</span>
              </div>
            </div>
          </div>

          {/* Full Lifecycle Terminal Demo */}
          <div className="mt-8 max-w-4xl mx-auto">
            <div className="bg-slate-950 rounded-lg shadow-2xl overflow-hidden border border-slate-700\/50">
              {/* Terminal Header */}
              <div className="flex items-center gap-2 px-4 py-3 bg-slate-800 border-slate-700\/50">
                <div style={{width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#ef4444'}} />
                <div style={{width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#f59e0b'}} />
                <div style={{width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#22c55e'}} />
                <span className="text-slate-400 text-xs ml-4 font-mono">
                  ~/my-project
                </span>
              </div>
              {/* Terminal Content */}
              <div className="p-6 font-mono text-sm space-y-4">
                <div>
                  <div className="text-slate-500"># Initialize AAM with curated community sources</div>
                  <div className="text-white">$ <span className="text-cyan-400">aam</span> init</div>
                  <div className="text-slate-400 mt-1">
                    Initialized AAM workspace in ~/my-project<br />
                    Added default source: <span className="text-emerald-400">openai/skills:.curated</span> (8 skills)<br />
                    Added default source: <span className="text-emerald-400">github/awesome-copilot</span> (15 skills)
                  </div>
                </div>

                <div>
                  <div className="text-slate-500"># Add Anthropic's Claude skills repository</div>
                  <div className="text-white">$ <span className="text-cyan-400">aam</span> source add anthropic/claude-skills</div>
                  <div className="text-slate-400 mt-1">
                    Cloning <span className="text-blue-400">https://github.com/anthropic/claude-skills</span> (shallow)...<br />
                    Scanning for artifacts...<br />
                    <span className="text-emerald-400">Found 16 skills, 3 agents, 2 prompts</span><br />
                    Source <span className="text-white">anthropic/claude-skills</span> added to config
                  </div>
                </div>

                <div>
                  <div className="text-slate-500"># Browse what's available — see candidates not yet packaged</div>
                  <div className="text-white">$ <span className="text-cyan-400">aam</span> source candidates --source anthropic/claude-skills --type skill</div>
                  <div className="text-slate-400 mt-1">
                    <span className="text-white">anthropic/claude-skills</span> (16 candidates)<br />
                    <span className="text-violet-400">  skill</span>  code-review &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Code review with Claude best practices<br />
                    <span className="text-violet-400">  skill</span>  refactor-py &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Python refactoring patterns<br />
                    <span className="text-violet-400">  skill</span>  test-gen &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Automated test generation<br />
                    <span className="text-violet-400">  skill</span>  doc-writer &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Documentation from code<br />
                    <span className="text-slate-500">  ... and 12 more</span>
                  </div>
                </div>

                <div>
                  <div className="text-slate-500"># Package two skills for your project</div>
                  <div className="text-white">$ <span className="text-cyan-400">aam</span> create-package --from-source anthropic/claude-skills --artifacts code-review,test-gen</div>
                  <div className="text-slate-400 mt-1">
                    Created <span className="text-emerald-400">@anthropic/code-review-skills</span> (aam.yaml + 5 files)<br />
                    Provenance: anthropic/claude-skills @ <span className="text-yellow-400">a3f7c2d</span><br />
                    Checksums: SHA-256 for all artifact files<br />
                    <span className="text-emerald-400">Package ready.</span> Run <span className="text-cyan-400">aam pkg pack</span> to create archive.
                  </div>
                </div>

                <div>
                  <div className="text-slate-500"># Later... check for upstream changes</div>
                  <div className="text-white">$ <span className="text-cyan-400">aam</span> source update --all</div>
                  <div className="text-slate-400 mt-1">
                    Fetching <span className="text-white">anthropic/claude-skills</span>...<br />
                    <span className="text-emerald-400">  + 2 new</span> &nbsp;
                    <span className="text-amber-400">~ 1 modified</span> &nbsp;
                    <span className="text-slate-500">= 16 unchanged</span><br />
                    Fetching <span className="text-white">openai/skills:.curated</span>...<br />
                    <span className="text-slate-500">  No changes (up to date)</span><br />
                    Fetching <span className="text-white">github/awesome-copilot</span>...<br />
                    <span className="text-emerald-400">  + 5 new</span> &nbsp;
                    <span className="text-red-400">- 1 removed</span> &nbsp;
                    <span className="text-slate-500">= 14 unchanged</span>
                  </div>
                </div>

                <div>
                  <div className="text-slate-500"># Verify nothing was tampered with locally</div>
                  <div className="text-white">$ <span className="text-cyan-400">aam</span> verify --all</div>
                  <div className="text-slate-400 mt-1">
                    <span className="text-emerald-400">All 5 files match installed checksums. No modifications detected.</span>
                  </div>
                </div>
              </div>
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

          {/* Extended Feature Grid for Git Source Management */}
          <div className="grid md:grid-cols-3 gap-8 mt-8">
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
                🌐
              </div>
              <h3 className="text-xl font-semibold mb-2">Git Source Tracking</h3>
              <p className="text-slate-600">
                Register any git repository as a skill source. Track upstream changes from
                OpenAI, Anthropic, GitHub, or your private repos.
              </p>
            </div>
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-amber-100 text-amber-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
                🔄
              </div>
              <h3 className="text-xl font-semibold mb-2">Change Detection</h3>
              <p className="text-slate-600">
                See exactly what's new, modified, or removed across all your tracked sources.
                Never miss an important update to the skills you depend on.
              </p>
            </div>
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
                🛡️
              </div>
              <h3 className="text-xl font-semibold mb-2">Integrity Verification</h3>
              <p className="text-slate-600">
                SHA-256 checksums for every file. Verify installed skills haven't been tampered
                with and view diffs before upgrading.
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
