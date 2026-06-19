import React, { useState, useEffect } from 'react';
import { useNavigate, Navigate, useLocation } from 'react-router-dom';
import { Loader, CheckCircle2, AlertTriangle, XCircle, Info, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Simple global toast trigger
let toastTrigger = null;
export const showToast = (message, type = 'success') => {
  if (toastTrigger) {
    toastTrigger(message, type);
  } else {
    console.log(`Toast fallback: [${type}] ${message}`);
  }
};

export default function ProtectedRoute({ children, theme, toggleTheme }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [toasts, setToasts] = useState([]);
  
  const navigate = useNavigate();
  const location = useLocation();
  const token = localStorage.getItem('token');

  // Register the global toast handler
  useEffect(() => {
    toastTrigger = (message, type) => {
      const id = Date.now() + Math.random().toString();
      setToasts(prev => [...prev, { id, message, type }]);
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== id));
      }, 4000);
    };
    return () => {
      toastTrigger = null;
    };
  }, []);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

    const fetchUser = async () => {
      try {
        const response = await fetch('/api/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (!response.ok) {
          throw new Error('Session expired.');
        }
        const data = await response.json();
        setUser(data);
      } catch (err) {
        console.error(err);
        localStorage.removeItem('token');
        navigate('/login');
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [token, navigate]);

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-page-bg">
        <div className="flex flex-col items-center gap-3 p-8 rounded-xl bg-white border border-border-light shadow-saas-lg">
          <Loader className="w-7 h-7 animate-spin text-primary" />
          <p className="text-sm font-medium text-text-muted">Loading your workspace...</p>
        </div>
      </div>
    );
  }

  // Inject user data and toast trigger to children
  const childrenWithUser = React.Children.map(children, child => {
    if (React.isValidElement(child)) {
      return React.cloneElement(child, { user });
    }
    return child;
  });

  const removeToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-page-bg text-text-primary font-sans overflow-hidden">
      <AnimatePresence mode="wait">
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15, ease: 'easeInOut' }}
          className="flex-1 h-full w-full flex flex-col"
        >
          {childrenWithUser}
        </motion.div>
      </AnimatePresence>

      {/* Toast Notifications Overlay */}
      <div className="fixed bottom-4 right-4 z-[9999] flex flex-col space-y-2 max-w-sm w-full pointer-events-none">
        <AnimatePresence>
          {toasts.map(toast => {
            const isSuccess = toast.type === 'success';
            const isError = toast.type === 'error';
            const isWarning = toast.type === 'warning';
            
            return (
              <motion.div
                key={toast.id}
                initial={{ opacity: 0, y: 20, scale: 0.9 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.9 }}
                className="pointer-events-auto w-full p-4 rounded-xl shadow-saas-lg border bg-white flex items-start space-x-3"
                style={{
                  borderColor: isSuccess ? '#CCFBF1' : isError ? '#FEE2E2' : isWarning ? '#FEF3C7' : '#E2E8F0'
                }}
              >
                <div className="shrink-0">
                  {isSuccess && <CheckCircle2 className="w-5 h-5 text-success" />}
                  {isError && <XCircle className="w-5 h-5 text-error" />}
                  {isWarning && <AlertTriangle className="w-5 h-5 text-amber-500" />}
                  {!isSuccess && !isError && !isWarning && <Info className="w-5 h-5 text-sky-500" />}
                </div>
                <div className="flex-1 text-sm font-bold text-accent/80 leading-snug">
                  {toast.message}
                </div>
                <button 
                  onClick={() => removeToast(toast.id)}
                  className="shrink-0 p-0.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
