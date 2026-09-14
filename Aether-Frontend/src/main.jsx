import React from 'react';
import ReactDOM from 'react-dom/client';
import CesiumViewer from './CesiumViewer';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <CesiumViewer />
  </React.StrictMode>
);
