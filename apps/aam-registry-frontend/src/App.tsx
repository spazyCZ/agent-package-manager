import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

/**
 * Root application component for AAM Registry Frontend.
 */
function App(): React.ReactElement {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 py-4 flex items-center gap-3">
            <h1 className="text-xl font-bold text-gray-900">AAM Registry</h1>
            <span className="text-sm text-gray-500">Agent Package Manager</span>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 py-8">
          <Routes>
            <Route
              path="/"
              element={
                <div className="text-center py-16">
                  <h2 className="text-3xl font-bold text-gray-800 mb-4">
                    Welcome to AAM Registry
                  </h2>
                  <p className="text-gray-600 text-lg">
                    Browse, publish, and manage AI agent artifacts.
                  </p>
                </div>
              }
            />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
