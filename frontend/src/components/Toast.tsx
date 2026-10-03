import React from 'react';
import { AlertCircle, CheckCircle2, Info, X } from 'lucide-react';

export interface ToastProps {
  type?: 'success' | 'error' | 'info';
  message: string;
  onClose?: () => void;
}

export const Toast: React.FC<ToastProps> = ({ type = 'info', message, onClose }) => {
  return (
    <div className={`toast-banner toast-${type}`}>
      <div className="toast-icon">
        {type === 'success' && <CheckCircle2 size={18} />}
        {type === 'error' && <AlertCircle size={18} />}
        {type === 'info' && <Info size={18} />}
      </div>
      <span className="toast-message">{message}</span>
      {onClose && (
        <button type="button" className="btn-toast-close" onClick={onClose} aria-label="Close notification">
          <X size={15} />
        </button>
      )}
    </div>
  );
};
