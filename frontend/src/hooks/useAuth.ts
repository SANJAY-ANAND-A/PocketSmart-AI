import { useContext } from 'react';
import type { AuthContextType } from '../context/authContextDef';
import { AuthContext } from '../context/authContextDef';

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
