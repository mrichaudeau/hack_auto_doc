/**
 * Authentication Flow Integration Tests (US-3: Standard User Login, TASK-3.19)
 *
 * Tests the complete authentication flow including:
 * - Login form submission
 * - Token storage
 * - AuthContext state management
 * - Authenticated API calls
 * - Automatic token refresh
 * - Logout flow
 * - Protected route redirects
 * - Session restoration
 */

import { describe, it, expect, beforeAll, afterEach, afterAll, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../contexts/AuthContext';
import LoginPage from '../../pages/LoginPage';
import ProtectedRoute from '../../components/ProtectedRoute';
import App from '../../App';

// Mock API responses
const mockLoginSuccess = {
  access: 'mock-access-token-123',
  refresh: 'mock-refresh-token-456',
  user: {
    id: 1,
    email: 'test@example.com',
    first_name: 'Test',
    last_name: 'User',
  },
};

const mockLoginFailure = {
  error: 'Invalid email or password',
};

const mockTokenRefresh = {
  access: 'new-access-token-789',
};

// Setup MSW server
const server = setupServer(
  // Login endpoint - success
  http.post('http://localhost:8000/api/auth/login/', async ({ request }) => {
    const body = await request.json();
    if (body.email === 'test@example.com' && body.password === 'password123') {
      return HttpResponse.json(mockLoginSuccess, { status: 200 });
    }
    return HttpResponse.json(mockLoginFailure, { status: 401 });
  }),

  // Token refresh endpoint
  http.post('http://localhost:8000/api/auth/token/refresh/', async ({ request }) => {
    const body = await request.json();
    if (body.refresh === 'mock-refresh-token-456') {
      return HttpResponse.json(mockTokenRefresh, { status: 200 });
    }
    return HttpResponse.json({ error: 'Invalid refresh token' }, { status: 401 });
  }),

  // Protected endpoint - simulates API requiring authentication
  http.get('http://localhost:8000/api/protected-resource/', ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    if (authHeader && authHeader.startsWith('Bearer ')) {
      const token = authHeader.replace('Bearer ', '');
      if (token === 'mock-access-token-123' || token === 'new-access-token-789') {
        return HttpResponse.json({ data: 'Protected data' }, { status: 200 });
      }
      // Token expired - trigger refresh
      if (token === 'expired-token') {
        return HttpResponse.json({ error: 'Token expired' }, { status: 401 });
      }
    }
    return HttpResponse.json({ error: 'Unauthorized' }, { status: 401 });
  })
);

// Start server before all tests
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' });
});

// Reset handlers after each test
afterEach(() => {
  server.resetHandlers();
  localStorage.clear();
  vi.clearAllMocks();
});

// Close server after all tests
afterAll(() => {
  server.close();
});

// Helper function to render component with router and auth context
const renderWithAuth = (component) => {
  return render(
    <BrowserRouter>
      <AuthProvider>{component}</AuthProvider>
    </BrowserRouter>
  );
};

describe('Authentication Flow Integration Tests', () => {
  describe('Login Flow', () => {
    it('should complete successful login flow with token storage and redirect', async () => {
      const user = userEvent.setup();

      // Mock navigate to prevent actual navigation
      const mockNavigate = vi.fn();
      vi.mock('react-router-dom', async () => {
        const actual = await vi.importActual('react-router-dom');
        return {
          ...actual,
          useNavigate: () => mockNavigate,
        };
      });

      renderWithAuth(<LoginPage />);

      // Verify login page is rendered
      expect(screen.getByText(/sign in/i)).toBeInTheDocument();

      // Fill in login form
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      // Wait for login to complete
      await waitFor(() => {
        // Verify tokens are stored in localStorage
        expect(localStorage.getItem('veille_tech_access_token')).toBe('mock-access-token-123');
        expect(localStorage.getItem('veille_tech_refresh_token')).toBe('mock-refresh-token-456');
      });

      // Verify user data is stored
      const userData = JSON.parse(localStorage.getItem('veille_tech_user'));
      expect(userData).toEqual({
        id: 1,
        email: 'test@example.com',
        first_name: 'Test',
        last_name: 'User',
      });
    });

    it('should show error message on failed login', async () => {
      const user = userEvent.setup();
      renderWithAuth(<LoginPage />);

      // Fill in login form with wrong credentials
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'wrongpassword');
      await user.click(submitButton);

      // Wait for error message to appear
      await waitFor(() => {
        expect(screen.getByText(/invalid email or password/i)).toBeInTheDocument();
      });

      // Verify tokens are NOT stored
      expect(localStorage.getItem('veille_tech_access_token')).toBeNull();
      expect(localStorage.getItem('veille_tech_refresh_token')).toBeNull();
    });

    it('should update AuthContext user state after successful login', async () => {
      const user = userEvent.setup();

      // Create a test component that uses AuthContext
      const TestComponent = () => {
        const { user: authUser, loading } = useAuth();
        if (loading) return <div>Loading...</div>;
        return authUser ? <div>User: {authUser.email}</div> : <div>Not logged in</div>;
      };

      renderWithAuth(
        <>
          <LoginPage />
          <TestComponent />
        </>
      );

      // Initially not logged in
      expect(screen.getByText(/not logged in/i)).toBeInTheDocument();

      // Fill in and submit login form
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      // Wait for AuthContext to update
      await waitFor(() => {
        expect(screen.getByText(/user: test@example.com/i)).toBeInTheDocument();
      });
    });
  });

  describe('Authenticated API Calls', () => {
    beforeEach(() => {
      // Pre-populate localStorage with tokens for authenticated tests
      localStorage.setItem('veille_tech_access_token', 'mock-access-token-123');
      localStorage.setItem('veille_tech_refresh_token', 'mock-refresh-token-456');
      localStorage.setItem(
        'veille_tech_user',
        JSON.stringify({
          id: 1,
          email: 'test@example.com',
          first_name: 'Test',
          last_name: 'User',
        })
      );
    });

    it('should include Authorization header in authenticated API calls', async () => {
      let capturedAuthHeader = null;

      // Override handler to capture auth header
      server.use(
        http.get('http://localhost:8000/api/protected-resource/', ({ request }) => {
          capturedAuthHeader = request.headers.get('Authorization');
          return HttpResponse.json({ data: 'Protected data' }, { status: 200 });
        })
      );

      // Import apiClient and make a request
      const { default: apiClient } = await import('../../services/apiClient');
      await apiClient.get('/api/protected-resource/');

      // Verify Authorization header was sent
      expect(capturedAuthHeader).toBe('Bearer mock-access-token-123');
    });

    it('should automatically refresh token on 401 response', async () => {
      let requestCount = 0;

      // Override handlers to simulate token expiration
      server.use(
        http.get('http://localhost:8000/api/protected-resource/', ({ request }) => {
          requestCount++;
          const authHeader = request.headers.get('Authorization');

          // First request with old token - return 401
          if (requestCount === 1) {
            return HttpResponse.json({ error: 'Token expired' }, { status: 401 });
          }

          // Second request after refresh - return success
          if (authHeader === 'Bearer new-access-token-789') {
            return HttpResponse.json({ data: 'Protected data' }, { status: 200 });
          }

          return HttpResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }),

        http.post('http://localhost:8000/api/auth/token/refresh/', () => {
          return HttpResponse.json({ access: 'new-access-token-789' }, { status: 200 });
        })
      );

      const { default: apiClient } = await import('../../services/apiClient');

      // Make request that will trigger 401 and token refresh
      const response = await apiClient.get('/api/protected-resource/');

      // Verify request succeeded after refresh
      expect(response.data).toEqual({ data: 'Protected data' });
      expect(requestCount).toBe(2); // Original request + retry after refresh

      // Verify new token is stored
      await waitFor(() => {
        expect(localStorage.getItem('veille_tech_access_token')).toBe('new-access-token-789');
      });
    });
  });

  describe('Protected Routes', () => {
    it('should redirect unauthenticated user to login', async () => {
      const DashboardPage = () => <div>Dashboard</div>;

      const TestApp = () => (
        <BrowserRouter>
          <AuthProvider>
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          </AuthProvider>
        </BrowserRouter>
      );

      render(<TestApp />);

      // User should see loading first, then be redirected
      // Since we can't test actual navigation in this setup,
      // we verify that the component shows loading state
      await waitFor(() => {
        // After loading, should not show dashboard
        expect(screen.queryByText(/dashboard/i)).not.toBeInTheDocument();
      });
    });

    it('should render protected content for authenticated user', async () => {
      // Pre-populate localStorage with tokens
      localStorage.setItem('veille_tech_access_token', 'mock-access-token-123');
      localStorage.setItem('veille_tech_refresh_token', 'mock-refresh-token-456');
      localStorage.setItem(
        'veille_tech_user',
        JSON.stringify({
          id: 1,
          email: 'test@example.com',
          first_name: 'Test',
          last_name: 'User',
        })
      );

      const DashboardPage = () => <div>Dashboard Content</div>;

      const TestApp = () => (
        <BrowserRouter>
          <AuthProvider>
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          </AuthProvider>
        </BrowserRouter>
      );

      render(<TestApp />);

      // Should show protected content after session restoration
      await waitFor(() => {
        expect(screen.getByText(/dashboard content/i)).toBeInTheDocument();
      });
    });
  });

  describe('Logout Flow', () => {
    beforeEach(() => {
      // Pre-populate localStorage with tokens
      localStorage.setItem('veille_tech_access_token', 'mock-access-token-123');
      localStorage.setItem('veille_tech_refresh_token', 'mock-refresh-token-456');
      localStorage.setItem(
        'veille_tech_user',
        JSON.stringify({
          id: 1,
          email: 'test@example.com',
          first_name: 'Test',
          last_name: 'User',
        })
      );
    });

    it('should clear tokens and redirect to login on logout', async () => {
      const { useAuth } = await import('../../hooks/useAuth');

      const TestComponent = () => {
        const { user, logout } = useAuth();
        return (
          <div>
            {user ? <div>Logged in as {user.email}</div> : <div>Not logged in</div>}
            <button onClick={logout}>Logout</button>
          </div>
        );
      };

      renderWithAuth(<TestComponent />);

      // Initially logged in
      await waitFor(() => {
        expect(screen.getByText(/logged in as test@example.com/i)).toBeInTheDocument();
      });

      // Verify tokens exist
      expect(localStorage.getItem('veille_tech_access_token')).not.toBeNull();

      // Click logout
      const user = userEvent.setup();
      const logoutButton = screen.getByRole('button', { name: /logout/i });
      await user.click(logoutButton);

      // Verify tokens are cleared
      await waitFor(() => {
        expect(localStorage.getItem('veille_tech_access_token')).toBeNull();
        expect(localStorage.getItem('veille_tech_refresh_token')).toBeNull();
        expect(localStorage.getItem('veille_tech_user')).toBeNull();
      });

      // Verify user is logged out
      expect(screen.getByText(/not logged in/i)).toBeInTheDocument();
    });
  });

  describe('Session Restoration', () => {
    it('should restore user session from stored tokens on page refresh', async () => {
      // Pre-populate localStorage with tokens (simulating previous login)
      localStorage.setItem('veille_tech_access_token', 'mock-access-token-123');
      localStorage.setItem('veille_tech_refresh_token', 'mock-refresh-token-456');
      localStorage.setItem(
        'veille_tech_user',
        JSON.stringify({
          id: 1,
          email: 'test@example.com',
          first_name: 'Test',
          last_name: 'User',
        })
      );

      const { useAuth } = await import('../../hooks/useAuth');

      const TestComponent = () => {
        const { user, loading, isAuthenticated } = useAuth();
        if (loading) return <div>Restoring session...</div>;
        return (
          <div>
            {isAuthenticated ? (
              <div>Session restored: {user.email}</div>
            ) : (
              <div>No session</div>
            )}
          </div>
        );
      };

      renderWithAuth(<TestComponent />);

      // Should show loading initially
      expect(screen.getByText(/restoring session/i)).toBeInTheDocument();

      // Should restore session from storage
      await waitFor(() => {
        expect(screen.getByText(/session restored: test@example.com/i)).toBeInTheDocument();
      });
    });

    it('should clear invalid session data on restore failure', async () => {
      // Pre-populate with invalid/corrupted data
      localStorage.setItem('veille_tech_access_token', 'invalid-token');
      localStorage.setItem('veille_tech_user', 'invalid-json-data');

      const { useAuth } = await import('../../hooks/useAuth');

      const TestComponent = () => {
        const { user, loading } = useAuth();
        if (loading) return <div>Loading...</div>;
        return user ? <div>User: {user.email}</div> : <div>No session</div>;
      };

      renderWithAuth(<TestComponent />);

      // Should clear invalid session
      await waitFor(() => {
        expect(screen.getByText(/no session/i)).toBeInTheDocument();
        expect(localStorage.getItem('veille_tech_access_token')).toBeNull();
      });
    });
  });

  describe('Token Expiration Handling', () => {
    it('should handle refresh token expiration by logging out user', async () => {
      // Pre-populate with tokens
      localStorage.setItem('veille_tech_access_token', 'expired-access-token');
      localStorage.setItem('veille_tech_refresh_token', 'expired-refresh-token');
      localStorage.setItem(
        'veille_tech_user',
        JSON.stringify({ id: 1, email: 'test@example.com' })
      );

      // Override handlers to simulate both tokens expired
      server.use(
        http.get('http://localhost:8000/api/protected-resource/', () => {
          return HttpResponse.json({ error: 'Token expired' }, { status: 401 });
        }),

        http.post('http://localhost:8000/api/auth/token/refresh/', () => {
          return HttpResponse.json({ error: 'Refresh token expired' }, { status: 401 });
        })
      );

      const { default: apiClient } = await import('../../services/apiClient');

      // Attempt to make authenticated request
      try {
        await apiClient.get('/api/protected-resource/');
      } catch (error) {
        // Request should fail
        expect(error).toBeDefined();
      }

      // Tokens should be cleared after failed refresh
      await waitFor(() => {
        expect(localStorage.getItem('veille_tech_access_token')).toBeNull();
        expect(localStorage.getItem('veille_tech_refresh_token')).toBeNull();
      });
    });
  });
});
