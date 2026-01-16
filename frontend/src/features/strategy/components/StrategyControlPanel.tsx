import React from 'react';
import {
  Box,
  Typography,
  Slider,
  Stack,
  alpha,
  useTheme,
  Tooltip,
  IconButton,
} from '@mui/material';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';

interface StrategyControlPanelProps {
  riskLevel: number;
  setRiskLevel: (v: number) => void;
  confidence: number;
  setConfidence: (v: number) => void;
  stopLoss: number;
  setStopLoss: (v: number) => void;
}

const StrategyControlPanel: React.FC<StrategyControlPanelProps> = ({
  riskLevel,
  setRiskLevel,
  confidence,
  setConfidence,
  stopLoss,
  setStopLoss,
}) => {
  const theme = useTheme();

  return (
    <Stack spacing={4} sx={{ p: 2 }}>
      <Box>
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            Risk Tolerance
            <Tooltip title="Higher risk increases volatility and potential returns">
              <InfoOutlinedIcon sx={{ fontSize: 16, cursor: 'pointer' }} />
            </Tooltip>
          </Typography>
          <Typography variant="subtitle2" color="primary.main" fontWeight="bold">
            {riskLevel}/10
          </Typography>
        </Stack>
        <Slider
          value={riskLevel}
          min={1}
          max={10}
          onChange={(_, v) => setRiskLevel(v as number)}
          valueLabelDisplay="auto"
        />
      </Box>

      <Box>
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            ML Confidence Threshold
            <Tooltip title="Minimum probability required for the model to execute a trade">
              <InfoOutlinedIcon sx={{ fontSize: 16, cursor: 'pointer' }} />
            </Tooltip>
          </Typography>
          <Typography variant="subtitle2" color="secondary.main" fontWeight="bold">
            {Math.round(confidence * 100)}%
          </Typography>
        </Stack>
        <Slider
          value={confidence}
          min={0.5}
          max={0.99}
          step={0.01}
          onChange={(_, v) => setConfidence(v as number)}
          color="secondary"
          valueLabelDisplay="auto"
        />
      </Box>

      <Box>
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            Hard Stop-Loss
            <Tooltip title="Max allowable loss per trade before automatic exit">
              <InfoOutlinedIcon sx={{ fontSize: 16, cursor: 'pointer' }} />
            </Tooltip>
          </Typography>
          <Typography variant="subtitle2" color="error.main" fontWeight="bold">
            {Math.round(stopLoss * 100)}%
          </Typography>
        </Stack>
        <Slider
          value={stopLoss}
          min={0.01}
          max={0.1}
          step={0.01}
          onChange={(_, v) => setStopLoss(v as number)}
          sx={{ color: theme.palette.error.main }}
          valueLabelDisplay="auto"
        />
      </Box>
    </Stack>
  );
};

export default StrategyControlPanel;
