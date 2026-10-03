import React, { useState } from 'react';
import { Mail, Lock, User as UserIcon, AlertCircle, ArrowRight, CheckCircle2, Sparkles } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

interface AuthPageProps {
  onAuthSuccess?: () => void;
}

export const AuthPage: React.FC<AuthPageProps> = ({ onAuthSuccess }) => {
  const { login, register, error, clearError, isLoading } = useAuth();
  const [mode, setMode] = useState<'login' | 'register'>('login');

  // Login form state
  const [loginIdentifier, setLoginIdentifier] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  // Register form state
  const [registerEmail, setRegisterEmail] = useState('');
  const [registerUsername, setRegisterUsername] = useState('');
  const [registerFullName, setRegisterFullName] = useState('');
  const [registerPassword, setRegisterPassword] = useState('');

  // Client-side validation state
  const [clientError, setClientError] = useState<string | null>(null);

  const handleTabSwitch = (newMode: 'login' | 'register') => {
    setMode(newMode);
    setClientError(null);
    clearError();
  };

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setClientError(null);
    clearError();

    if (!loginIdentifier.trim()) {
      setClientError('Please enter your username or registered email.');
      return;
    }
    if (!loginPassword) {
      setClientError('Please enter your account password.');
      return;
    }

    try {
      await login({
        username_or_email: loginIdentifier.trim(),
        password: loginPassword,
      });
      if (onAuthSuccess) {
        onAuthSuccess();
      }
    } catch {
      // Backend error is stored in context and rendered below
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setClientError(null);
    clearError();

    // Client-side validation
    if (!registerEmail.trim() || !registerEmail.includes('@')) {
      setClientError('Please enter a valid email address.');
      return;
    }
    if (!registerUsername.trim() || registerUsername.trim().length < 3) {
      setClientError('Username must be at least 3 characters long.');
      return;
    }
    if (!/^[a-zA-Z0-9_-]+$/.test(registerUsername.trim())) {
      setClientError('Username can only contain letters, numbers, hyphens, and underscores.');
      return;
    }
    if (!registerPassword || registerPassword.length < 6) {
      setClientError('Password must be at least 6 characters long.');
      return;
    }

    try {
      await register({
        email: registerEmail.trim(),
        username: registerUsername.trim(),
        full_name: registerFullName.trim() || undefined,
        password: registerPassword,
      });
      if (onAuthSuccess) {
        onAuthSuccess();
      }
    } catch {
      // Error is caught and displayed from context
    }
  };

  const activeError = clientError || error;

  return (
    <div className="auth-page-wrapper">
      <div className="auth-card">
        {/* Card Header */}
        <div className="auth-header">
          <div className="auth-icon-badge">
            <Sparkles size={24} className="accent-sparkle" />
          </div>
          <h2 className="auth-title">
            {mode === 'login' ? 'Welcome Back' : 'Create Account'}
          </h2>
          <p className="auth-subtitle">
            {mode === 'login'
              ? 'Sign in to access your intelligent budget plans and recommendations'
              : 'Join PocketSmart AI to start planning your smart budgets'}
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="auth-tabs">
          <button
            type="button"
            className={`auth-tab ${mode === 'login' ? 'active' : ''}`}
            onClick={() => handleTabSwitch('login')}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`auth-tab ${mode === 'register' ? 'active' : ''}`}
            onClick={() => handleTabSwitch('register')}
          >
            Create Account
          </button>
        </div>

        {/* Error Alert */}
        {activeError && (
          <div className="auth-alert error">
            <AlertCircle size={18} className="alert-icon" />
            <span className="alert-text">{activeError}</span>
          </div>
        )}

        {/* Login Form */}
        {mode === 'login' ? (
          <form onSubmit={handleLoginSubmit} className="auth-form">
            <div className="form-group">
              <label htmlFor="login-identifier" className="form-label">
                Username or Email
              </label>
              <div className="input-with-icon">
                <Mail size={18} className="input-icon" />
                <input
                  id="login-identifier"
                  type="text"
                  className="form-input"
                  placeholder="e.g. demo_student or email@example.com"
                  value={loginIdentifier}
                  onChange={(e) => setLoginIdentifier(e.target.value)}
                  disabled={isLoading}
                  autoComplete="username"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="login-password" className="form-label">
                Password
              </label>
              <div className="input-with-icon">
                <Lock size={18} className="input-icon" />
                <input
                  id="login-password"
                  type="password"
                  className="form-input"
                  placeholder="Enter your password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  disabled={isLoading}
                  autoComplete="current-password"
                />
              </div>
            </div>

            <button type="submit" className="btn-primary-auth" disabled={isLoading}>
              {isLoading ? (
                <span className="btn-spinner">Signing in...</span>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>
        ) : (
          /* Register Form */
          <form onSubmit={handleRegisterSubmit} className="auth-form">
            <div className="form-group">
              <label htmlFor="register-email" className="form-label">
                Email Address <span className="required">*</span>
              </label>
              <div className="input-with-icon">
                <Mail size={18} className="input-icon" />
                <input
                  id="register-email"
                  type="email"
                  className="form-input"
                  placeholder="student@pocketsmart.ai"
                  value={registerEmail}
                  onChange={(e) => setRegisterEmail(e.target.value)}
                  disabled={isLoading}
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="register-username" className="form-label">
                Username <span className="required">*</span>
              </label>
              <div className="input-with-icon">
                <UserIcon size={18} className="input-icon" />
                <input
                  id="register-username"
                  type="text"
                  className="form-input"
                  placeholder="e.g. smart_planner (letters, numbers, _)"
                  value={registerUsername}
                  onChange={(e) => setRegisterUsername(e.target.value)}
                  disabled={isLoading}
                  autoComplete="username"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="register-fullname" className="form-label">
                Full Name <span className="optional">(optional)</span>
              </label>
              <div className="input-with-icon">
                <UserIcon size={18} className="input-icon" />
                <input
                  id="register-fullname"
                  type="text"
                  className="form-input"
                  placeholder="e.g. College Student"
                  value={registerFullName}
                  onChange={(e) => setRegisterFullName(e.target.value)}
                  disabled={isLoading}
                  autoComplete="name"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="register-password" className="form-label">
                Password <span className="required">*</span>
              </label>
              <div className="input-with-icon">
                <Lock size={18} className="input-icon" />
                <input
                  id="register-password"
                  type="password"
                  className="form-input"
                  placeholder="Minimum 6 characters"
                  value={registerPassword}
                  onChange={(e) => setRegisterPassword(e.target.value)}
                  disabled={isLoading}
                  autoComplete="new-password"
                  required
                />
              </div>
            </div>

            <button type="submit" className="btn-primary-auth" disabled={isLoading}>
              {isLoading ? (
                <span className="btn-spinner">Creating account...</span>
              ) : (
                <>
                  <span>Create Account</span>
                  <CheckCircle2 size={18} />
                </>
              )}
            </button>
          </form>
        )}

        {/* Demo Credentials Helper */}
        <div className="demo-credentials-card">
          <span className="demo-label">CapStone Demo Quick-Fill:</span>
          <p className="demo-text">
            Register a new account or use any registered credentials.
          </p>
        </div>
      </div>
    </div>
  );
};
