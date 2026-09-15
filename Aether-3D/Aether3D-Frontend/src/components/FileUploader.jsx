import React, { useState, useCallback } from 'react';
import {
  Card,
  Button,
  Text,
  Spinner,
} from '@fluentui/react-components';
import {
  Folder24Regular,
  ArrowUpload24Regular,
  Play24Regular,
} from '@fluentui/react-icons';
import { validateCzml } from '@utils/czmlUtils.js';
import './FileUploader.css';

export default function FileUploader({ onCzmlLoad }) {
  const [isDragging, setIsDragging] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [isLoadingSample, setIsLoadingSample] = useState(false);

  const processCzmlText = useCallback(
    (text, fileName) => {
      try {
        const parsed = JSON.parse(text);
        const { valid, error } = validateCzml(parsed);
        if (!valid) {
          setErrorMessage(`Invalid CZML file: ${error}`);
          return;
        }
        setErrorMessage(null);
        onCzmlLoad(parsed, fileName);
      } catch {
        setErrorMessage('Failed to parse file: Not valid JSON');
      }
    },
    [onCzmlLoad]
  );

  const readCzmlFile = useCallback(
    (file) => {
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (e) => processCzmlText(e.target.result, file.name);
      reader.onerror = () => setErrorMessage('Failed to read file from disk');
      reader.readAsText(file);
    },
    [processCzmlText]
  );

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) readCzmlFile(file);
    },
    [readCzmlFile]
  );

  const handleFileChange = useCallback(
    (e) => {
      const file = e.target.files[0];
      if (file) readCzmlFile(file);
      e.target.value = '';
    },
    [readCzmlFile]
  );

  const handleLoadSample = useCallback(async () => {
    setIsLoadingSample(true);
    setErrorMessage(null);
    try {
      const res = await fetch('/sample.czml');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const text = await res.text();
      processCzmlText(text, 'sample.czml');
    } catch (err) {
      setErrorMessage(`Failed to load sample dataset: ${err.message}`);
    } finally {
      setIsLoadingSample(false);
    }
  }, [processCzmlText]);

  return (
    <Card className="file-uploader-section">
      <Text weight="semibold" size={300} className="section-title">
        Data Source
      </Text>
      <div
        className={`drop-zone ${isDragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <Folder24Regular className="drop-icon" />
        <Text size={200} className="drop-text">
          Drag & drop CZML dataset here
        </Text>
        <label className="file-select-btn">
          <Button icon={<ArrowUpload24Regular />} appearance="outline" size="small">
            Browse File
          </Button>
          <input type="file" accept=".czml,.json" onChange={handleFileChange} />
        </label>
      </div>

      <Button
        appearance="primary"
        icon={isLoadingSample ? <Spinner size="tiny" /> : <Play24Regular />}
        onClick={handleLoadSample}
        disabled={isLoadingSample}
        className="sample-btn"
      >
        {isLoadingSample ? 'Loading Demo…' : 'Load Sample Data'}
      </Button>

      {errorMessage && <div className="uploader-error">⚠ {errorMessage}</div>}
    </Card>
  );
}
