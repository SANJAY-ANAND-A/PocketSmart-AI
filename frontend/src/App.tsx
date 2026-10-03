import React, { useState } from 'react';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './hooks/useAuth';
import { Navbar, type NavTab } from './components/Navbar';
import { Footer } from './components/Footer';
import { AuthPage } from './pages/AuthPage';
import { HomePlannerPage } from './pages/HomePlannerPage';
import { PartyPlannerPage } from './pages/PartyPlannerPage';
import { JewelryPlannerPage } from './pages/JewelryPlannerPage';
import { SavedPlansPage } from './pages/SavedPlansPage';
import { CatalogPage } from './pages/CatalogPage';
import { Lock, ArrowRight } from 'lucide-react';
import './App.css';

const MainShell: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState<NavTab>('catalog');

  const renderContent = () => {
    // 1. Auth Page
    if (activeTab === 'auth') {
      if (isAuthenticated) {
        setActiveTab('catalog');
        return null;
      }
      return <AuthPage onAuthSuccess={() => setActiveTab('catalog')} />;
    }

    // 2. Protected Tabs Guarding Check
    const isProtected = ['home', 'party', 'jewelry', 'plans'].includes(activeTab);
    if (isProtected && !isAuthenticated) {
      return (
        <div className="auth-required-wrapper">
          <div className="auth-required-banner">
            <div className="auth-required-info">
              <Lock size={24} className="auth-required-icon" />
              <div>
                <h3 className="auth-required-title">Authentication Required</h3>
                <p className="auth-required-text">
                  Please sign in or create a free account to access personalized AI planners and saved budget history.
                </p>
              </div>
            </div>
            <button
              type="button"
              className="btn-signin"
              onClick={() => setActiveTab('auth')}
            >
              <span>Sign In / Register</span>
              <ArrowRight size={16} />
            </button>
          </div>
          <AuthPage onAuthSuccess={() => setActiveTab(activeTab)} />
        </div>
      );
    }

    // 3. Home Interior Planner (Phase 11B Complete Page)
    if (activeTab === 'home') {
      return <HomePlannerPage onNavigateToPlans={() => setActiveTab('plans')} />;
    }

    // 4. Party / Event Planner (Phase 11B Complete Page)
    if (activeTab === 'party') {
      return <PartyPlannerPage onNavigateToPlans={() => setActiveTab('plans')} />;
    }

    // 5. Jewelry Planner (Phase 11B Complete Page with Multimodal Vision)
    if (activeTab === 'jewelry') {
      return <JewelryPlannerPage onNavigateToPlans={() => setActiveTab('plans')} />;
    }

    // 6. Saved Plans / History Dashboard (Phase 11B Complete Page)
    if (activeTab === 'plans') {
      return (
        <SavedPlansPage
          onNavigateToPlanner={(module) => setActiveTab(module)}
        />
      );
    }

    // 7. Product Catalog Explorer (Phase 11B Complete Page)
    return <CatalogPage />;
  };

  return (
    <div className="app-container">
      <Navbar activeTab={activeTab} onSelectTab={setActiveTab} />
      <main className="main-content">{renderContent()}</main>
      <Footer />
    </div>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <MainShell />
    </AuthProvider>
  );
}
