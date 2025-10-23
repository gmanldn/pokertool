import React from 'react';
import { Button } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';

/**
 * Export logs to file
 */
export const LogExporter: React.FC = () => {
  const exportLogs = (format: string) => {
    // Stub implementation
    const logs = [{type: 'info', message: 'Sample log'}];
    const dataStr = format === 'json' ? JSON.stringify(logs, null, 2) : logs.map(l => `${l.type}: ${l.message}`).join('\n');
    const dataUri = 'data:application/octet-stream;charset=utf-8,' + encodeURIComponent(dataStr);
    
    const link = document.createElement('a');
    link.setAttribute('href', dataUri);
    link.setAttribute('download', `logs.${format}`);
    link.click();
  };

  return (
    <div>
      <Button startIcon={<DownloadIcon />} onClick={() => exportLogs('json')}>
        Export JSON
      </Button>
      <Button startIcon={<DownloadIcon />} onClick={() => exportLogs('txt')}>
        Export TXT
      </Button>
    </div>
  );
};
