import React, { useState } from 'react';
import {
  Sparkles,
  Home,
  PartyPopper,
  Gem,
  BookmarkCheck,
  ShoppingBag,
  User as UserIcon,
  LogOut,
  LogIn,
  Menu,
  X,
  Lock,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export type NavTab = 'home' | 'party' | 'jewelry' | 'plans' | 'catalog' | 'auth';

interface NavbarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, onSelectTab }) => {
  const { user, isAuthenticated, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleTabClick = (tab: NavTab, requiresAuth: boolean) => {
    if (requiresAuth && !isAuthenticated) {
      onSelectTab('auth');
    } else {
      onSelectTab(tab);
    }
    setMobileMenuOpen(false);
  };

  const navItems = [
    { id: 'home' as NavTab, label: 'Home Interior', icon: Home, requiresAuth: true },
    { id: 'party' as NavTab, label: 'Party & Event', icon: PartyPopper, requiresAuth: true },
    { id: 'jewelry' as NavTab, label: 'Jewelry', icon: Gem, requiresAuth: true },
    { id: 'plans' as NavTab, label: 'Saved Plans', icon: BookmarkCheck, requiresAuth: true },
    { id: 'catalog' as NavTab, label: 'Catalog', icon: ShoppingBag, requiresAuth: false },
  ];

  return (
    <header className="navbar-container">
      <div className="navbar-content">
        {/* Brand Logo */}
        <div
          className="brand-logo"
          onClick={() => handleTabClick('catalog', false)}
          role="button"
          tabIndex={0}
        >
          <div className="brand-icon-wrapper">
            <Sparkles className="brand-icon" size={20} />
          </div>
          <div className="brand-text">
            <span className="brand-title">PocketSmart <span className="brand-ai">AI</span></span>
            <span className="brand-tagline">Smart Budget & Recommendations</span>
          </div>
        </div>

        {/* Desktop Navigation Links */}
        <nav className="desktop-nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            const isLocked = item.requiresAuth && !isAuthenticated;

            return (
              <button
                key={item.id}
                type="button"
                className={`nav-button ${isActive ? 'active' : ''}`}
                onClick={() => handleTabClick(item.id, item.requiresAuth)}
                title={isLocked ? `${item.label} (Sign in required)` : item.label}
              >
                <Icon size={16} className="nav-icon" />
                <span>{item.label}</span>
                {isLocked && <Lock size={12} className="lock-icon" />}
              </button>
            );
          })}
        </nav>

        {/* User Auth Section */}
        <div className="auth-section">
          {isAuthenticated && user ? (
            <div className="user-profile">
              <div className="user-badge" title={user.email}>
                <div className="user-avatar">
                  <UserIcon size={16} />
                </div>
                <div className="user-details">
                  <span className="user-name">{user.full_name || user.username}</span>
                  <span className="user-handle">@{user.username}</span>
                </div>
              </div>
              <button
                type="button"
                className="btn-logout"
                onClick={logout}
                title="Sign out of PocketSmart AI"
              >
                <LogOut size={16} />
                <span className="btn-text">Sign Out</span>
              </button>
            </div>
          ) : (
            <button
              type="button"
              className={`btn-signin ${activeTab === 'auth' ? 'active' : ''}`}
              onClick={() => {
                onSelectTab('auth');
                setMobileMenuOpen(false);
              }}
            >
              <LogIn size={16} />
              <span>Sign In</span>
            </button>
          )}

          {/* Mobile Menu Toggle Button */}
          <button
            type="button"
            className="mobile-menu-toggle"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="mobile-drawer">
          <div className="mobile-nav-items">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              const isLocked = item.requiresAuth && !isAuthenticated;

              return (
                <button
                  key={item.id}
                  type="button"
                  className={`mobile-nav-button ${isActive ? 'active' : ''}`}
                  onClick={() => handleTabClick(item.id, item.requiresAuth)}
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                  {isLocked && (
                    <span className="mobile-lock-badge">
                      <Lock size={12} /> Sign in
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          <div className="mobile-drawer-footer">
            {isAuthenticated && user ? (
              <div className="mobile-user-row">
                <div className="user-details">
                  <span className="user-name">{user.full_name || user.username}</span>
                  <span className="user-handle">{user.email}</span>
                </div>
                <button type="button" className="btn-logout mobile" onClick={logout}>
                  <LogOut size={16} />
                  <span>Sign Out</span>
                </button>
              </div>
            ) : (
              <button
                type="button"
                className="btn-signin mobile"
                onClick={() => {
                  onSelectTab('auth');
                  setMobileMenuOpen(false);
                }}
              >
                <LogIn size={16} />
                <span>Sign In / Create Account</span>
              </button>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
