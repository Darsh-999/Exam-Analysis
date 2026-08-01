import { createContext, useContext, useState } from 'react';

const AuthContext = createContext(null);

// Exported so apiClient.js can read the same token without duplicating the key.
export const TOKEN_KEY = 'examinsight_token';
const EMAIL_KEY = 'examinsight_email';

// Wrap the app in this once, near the top (see App.jsx). Any component below
// it can then call useAuth() to read the logged-in user or log in/out.
export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [userEmail, setUserEmail] = useState(() => localStorage.getItem(EMAIL_KEY));

  function login(newToken, email) {
    localStorage.setItem(TOKEN_KEY, newToken);
    localStorage.setItem(EMAIL_KEY, email);
    setToken(newToken);
    setUserEmail(email);
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(EMAIL_KEY);
    setToken(null);
    setUserEmail(null);
  }

  const value = {
    token,
    userEmail,
    isAuthenticated: Boolean(token),
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// oxlint-disable-next-line react/only-export-components
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside an <AuthProvider>');
  }
  return context;
}
