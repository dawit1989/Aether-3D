import React from 'react';
import {
  Text,
  Badge,
  Input,
} from '@fluentui/react-components';
import {
  Globe24Regular,
  PlugConnected24Regular,
  PlugDisconnected24Regular,
  ArrowSync24Regular,
} from '@fluentui/react-icons';
import { useApi, ApiStatus } from '@hooks/useApi.jsx';
import './StatusBar.css';

export default function StatusBar({ fileName, apiEndpoint, onApiEndpointChange }) {
  const { status } = useApi();

  return (
    <header className="status-bar">
      <div className="status-left">
        <Globe24Regular className="app-icon" />
        <Text weight="semibold" size={400} className="app-title">
          Aether-3D Viz
        </Text>
        <span className="status-divider">|</span>
        <Text size={300} className="file-info">
          {fileName ? `Dataset: ${fileName}` : 'No dataset loaded'}
        </Text>
      </div>

      <div className="status-right">
        <div className="api-config">
          <Text size={200} className="label">
            Backend API:
          </Text>
          <Input
            size="small"
            value={apiEndpoint}
            onChange={(e) => onApiEndpointChange?.(e.target.value)}
            placeholder="http://localhost:8000"
          />
          {status === ApiStatus.CONNECTED && (
            <Badge appearance="tint" color="success" icon={<PlugConnected24Regular />}>
              Online
            </Badge>
          )}
          {status === ApiStatus.DISCONNECTED && (
            <Badge appearance="tint" color="severe" icon={<PlugDisconnected24Regular />}>
              Offline
            </Badge>
          )}
          {status === ApiStatus.CHECKING && (
            <Badge appearance="tint" color="warning" icon={<ArrowSync24Regular />}>
              Checking
            </Badge>
          )}
        </div>
      </div>
    </header>
  );
}
