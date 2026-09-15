import React, { createContext, useContext, useState, useEffect } from 'react';

export const ApiStatus = {
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  CHECKING: 'checking',
};

const ApiContext = createContext({
  status: ApiStatus.CHECKING,
  endpoint: 'http://localhost:8000',
  checkHealth: async () => {},
});

export function ApiProvider({ children, endpoint = 'http://localhost:8000' }) {
  const [status, setStatus] = useState(ApiStatus.CHECKING);

  const checkHealth = async () => {
    setStatus(ApiStatus.CHECKING);
    try {
      const res = await fetch(`${endpoint}/health`, { method: 'GET', signal: AbortSignal.timeout(2000) });
      if (res.ok) {
        setStatus(ApiStatus.CONNECTED);
      } else {
        setStatus(ApiStatus.DISCONNECTED);
      }
    } catch {
      setStatus(ApiStatus.DISCONNECTED);
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, [endpoint]);

  return (
    <ApiContext.Provider value={{ status, endpoint, checkHealth }}>
      {children}
    </ApiContext.Provider>
  );
}

export function useApi() {
  return useContext(ApiContext);
}
