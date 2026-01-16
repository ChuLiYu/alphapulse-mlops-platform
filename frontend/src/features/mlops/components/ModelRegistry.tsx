import React, { useEffect, useState } from 'react';
import { 
  Box, 
  Typography, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Chip,
  alpha 
} from '@mui/material';
import apiClient from '../../../api/client';

const defaultModels = [
  { version: 'v2.4.1', stage: 'Production', accuracy: '89.2%', deployed: '2 days ago', status: 'Active' },
  { version: 'v2.5.0-rc1', stage: 'Staging', accuracy: '91.5%', deployed: '5 hours ago', status: 'Testing' },
  { version: 'v2.4.0', stage: 'Archived', accuracy: '87.8%', deployed: '14 days ago', status: 'Inactive' },
];

const ModelRegistry: React.FC = () => {
  const [models, setModels] = useState(defaultModels);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await apiClient.get('/v1/ops/models');
        if (response.data && response.data.models) {
          setModels(response.data.models);
        }
      } catch (error) {
        console.error('Failed to fetch models', error);
      }
    };
    fetchModels();
  }, []);

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>Model Registry & Deployment</Typography>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ color: 'text.secondary', fontWeight: 'bold' }}>Version</TableCell>
              <TableCell sx={{ color: 'text.secondary', fontWeight: 'bold' }}>Environment</TableCell>
              <TableCell sx={{ color: 'text.secondary', fontWeight: 'bold' }}>Accuracy</TableCell>
              <TableCell sx={{ color: 'text.secondary', fontWeight: 'bold' }}>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {models.map((model) => (
              <TableRow key={model.version} sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                <TableCell component="th" scope="row" sx={{ fontWeight: 'medium' }}>
                  {model.version}
                </TableCell>
                <TableCell>
                  <Chip 
                    label={model.stage} 
                    size="small" 
                    color={model.stage === 'Production' ? 'primary' : model.stage === 'Staging' ? 'warning' : 'default'}
                    variant="outlined"
                  />
                </TableCell>
                <TableCell>{model.accuracy}</TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ 
                      width: 8, 
                      height: 8, 
                      borderRadius: '50%', 
                      bgcolor: model.status === 'Active' ? 'secondary.main' : model.status === 'Testing' ? 'warning.main' : 'text.disabled' 
                    }} />
                    <Typography variant="body2">{model.status}</Typography>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default ModelRegistry;
