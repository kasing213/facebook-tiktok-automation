# Facebook/TikTok Automation Frontend

A React-based OAuth login interface for the Facebook/TikTok automation platform.

## Features

- **OAuth Integration**: Seamless Facebook and TikTok OAuth login flows
- **Responsive Design**: Mobile-friendly interface with modern styling
- **Real-time Status**: Live connection status for both platforms
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **TypeScript**: Full type safety throughout the application
- **Modern React**: Built with React 18, hooks, and modern patterns

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- FastAPI backend running on `http://localhost:8000`

### Installation

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   ```

   The application will be available at `http://localhost:3000`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── OAuthLoginPage.tsx    # Main login page
│   │   ├── OAuthCallback.tsx     # OAuth callback handler
│   │   ├── Dashboard.tsx         # Post-login dashboard
│   │   ├── LoadingSpinner.tsx    # Loading indicator
│   │   └── ErrorMessage.tsx      # Error display component
│   ├── hooks/              # Custom React hooks
│   │   └── useAuth.ts           # Authentication logic
│   ├── services/           # API services
│   │   └── api.ts              # FastAPI integration
│   ├── types/              # TypeScript definitions
│   │   └── auth.ts             # Authentication types
│   ├── App.tsx             # Main application component
│   ├── main.tsx            # Application entry point
│   └── index.css           # Global styles
├── public/
│   └── index.html          # HTML template
├── package.json            # Dependencies and scripts
├── vite.config.ts          # Vite configuration
└── tsconfig.json           # TypeScript configuration
```

## Key Components

### OAuthLoginPage
- Displays organization selector
- Provides Facebook and TikTok login buttons
- Shows current connection status
- Handles OAuth flow initiation

### OAuthCallback
- Processes OAuth callback responses
- Handles success and error states
- Redirects to dashboard on success

### Dashboard
- Displays detailed authentication status
- Shows connected accounts and token information
- Provides refresh functionality

## API Integration

The frontend integrates with the FastAPI backend through:

- **Health checks**: `/health`
- **Tenant management**: `/api/tenants`
- **OAuth flows**: `/oauth/facebook/*`, `/oauth/tiktok/*`
- **Status checks**: `/oauth/status/{tenant_id}`

## Configuration

### Vite Proxy Configuration

The development server is configured to proxy API requests to the FastAPI backend:

```typescript
proxy: {
  '/oauth': 'http://localhost:8000',
  '/api': 'http://localhost:8000',
  '/health': 'http://localhost:8000'
}
```

### Environment Variables

No environment variables are required for development as the API base URL is configured in the Vite proxy.

## OAuth Flow

1. **User Selection**: User selects organization from dropdown
2. **Platform Choice**: User clicks Facebook or TikTok login button
3. **OAuth Redirect**: Frontend redirects to FastAPI OAuth endpoint
4. **Platform Auth**: User authenticates with Facebook/TikTok
5. **Callback Processing**: Platform redirects back to frontend callback
6. **Token Storage**: FastAPI exchanges code for tokens and stores them
7. **Dashboard**: User is redirected to dashboard showing connection status

## Error Handling

The application includes comprehensive error handling for:

- Network failures
- OAuth errors
- Invalid responses
- Missing parameters
- Backend unavailability

## Responsive Design

The interface is fully responsive and works well on:

- Desktop computers
- Tablets
- Mobile phones

## TypeScript

The project uses TypeScript for type safety with:

- Strict type checking
- Interface definitions for all API responses
- Custom hooks with proper typing
- Component prop validation

## Development

### Code Style

- ESLint for code linting
- Prettier for code formatting
- TypeScript for type safety

### Hot Reload

The development server supports hot reload for instant development feedback.

## Browser Support

The application supports all modern browsers including:

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

This project is part of the Facebook/TikTok Automation platform.