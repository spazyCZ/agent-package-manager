# AAM Web

React web application for the Agent Package Manager registry.

## Installation

```bash
# From the monorepo root
npm install
```

## Running

```bash
# Development mode
npm run web

# Or using Nx
nx serve aam-web

# Or directly
cd apps/aam-web
npm run dev
```

The application will be available at http://localhost:3000

## Building

```bash
npm run web:build

# Or using Nx
nx build aam-web
```

Build output will be in `dist/apps/aam-web`.

## Features

- **Package Browser**: Search and browse available packages
- **Package Details**: View package information, versions, and documentation
- **User Authentication**: Login and registration
- **Modern UI**: Built with React and Tailwind CSS

## Tech Stack

- React 18
- TypeScript
- Vite
- React Router
- Tailwind CSS

## Project Structure

```
apps/aam-web/
├── public/           # Static assets
├── src/
│   ├── components/   # Reusable components
│   ├── pages/        # Page components
│   ├── styles/       # CSS styles
│   ├── test/         # Test setup
│   ├── App.tsx       # Main app component
│   └── main.tsx      # Entry point
├── index.html        # HTML template
├── vite.config.ts    # Vite configuration
├── tailwind.config.js # Tailwind configuration
└── tsconfig.json     # TypeScript configuration
```

## Development

The app proxies `/api` requests to the backend at `http://localhost:8000`.

### Testing

```bash
npm run web:test
```

### Linting

```bash
npm run web:lint
```
