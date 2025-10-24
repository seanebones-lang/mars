'use client';

import React, { useEffect, useRef, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Avatar,
  Paper,
  Tooltip,
  IconButton,
  Switch,
  FormControlLabel,
  Stack,
  Divider,
  Slider
} from '@mui/material';
import {
  CheckCircleOutlined,
  ErrorOutlined,
  WarningOutlined,
  ComputerOutlined,
  SpeedOutlined,
  MemoryOutlined,
  NotificationsOutlined,
  LocationOnOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  CenterFocusStrongOutlined,
  LayersOutlined,
  MapOutlined
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import dynamic from 'next/dynamic';

// Dynamically import Leaflet only on client-side
const loadLeaflet = async () => {
  if (typeof window !== 'undefined') {
    const L = await import('leaflet');
    // @ts-ignore
    await import('leaflet.heat');
    
    // Fix for default markers in Leaflet
    delete (L.default.Icon.Default.prototype as any)._getIconUrl;
    L.default.Icon.Default.mergeOptions({
      iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
      iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
    });
    
    return L.default;
  }
  return null;
};


interface Workstation {
  id: string;
  hostname: string;
  status: string;
  location: string;
  department: string;
  ipAddress: string;
  lastSeen: string;
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  agentCount: number;
  alertCount: number;
  platform: string;
  version: string;
  uptime: number;
  networkLatency: number;
  coordinates: {
    lat: number;
    lng: number;
  };
}

interface InteractiveWorldMapProps {
  workstations: Workstation[];
  onWorkstationSelect?: (workstation: Workstation) => void;
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'online': return '#4caf50';
    case 'monitoring': return '#2196f3';
    case 'offline': return '#9e9e9e';
    case 'error': return '#f44336';
    case 'maintenance': return '#ff9800';
    default: return '#9e9e9e';
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'online': return 'CheckCircleOutlined';
    case 'monitoring': return 'SpeedOutlined';
    case 'offline': return 'ComputerOutlined';
    case 'error': return 'ErrorOutlined';
    case 'maintenance': return 'WarningOutlined';
    default: return 'ComputerOutlined';
  }
};

const createCustomIcon = (status: string, alertCount: number, L: any) => {
  const color = getStatusColor(status);
  const hasAlerts = alertCount > 0;
  
  return L.divIcon({
    html: `
      <div style="
        position: relative;
        width: 24px;
        height: 24px;
        background: ${color};
        border: 2px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        ${hasAlerts ? 'animation: pulse 2s infinite;' : ''}
      ">
        <div style="
          width: 8px;
          height: 8px;
          background: white;
          border-radius: 50%;
        "></div>
        ${hasAlerts ? `
          <div style="
            position: absolute;
            top: -4px;
            right: -4px;
            width: 12px;
            height: 12px;
            background: #f44336;
            border: 1px solid white;
            border-radius: 50%;
            font-size: 8px;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
          ">${alertCount > 9 ? '9+' : alertCount}</div>
        ` : ''}
      </div>
      <style>
        @keyframes pulse {
          0% { box-shadow: 0 2px 8px rgba(0,0,0,0.3), 0 0 0 0 ${color}; }
          70% { box-shadow: 0 2px 8px rgba(0,0,0,0.3), 0 0 0 10px rgba(244, 67, 54, 0); }
          100% { box-shadow: 0 2px 8px rgba(0,0,0,0.3), 0 0 0 0 rgba(244, 67, 54, 0); }
        }
      </style>
    `,
    className: 'custom-workstation-marker',
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12]
  });
};

function InteractiveWorldMapComponent({ workstations, onWorkstationSelect }: InteractiveWorldMapProps) {
  const theme = useTheme();
  const mapRef = useRef<any>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const markersRef = useRef<any[]>([]);
  const heatmapLayerRef = useRef<any>(null);
  const [selectedWorkstation, setSelectedWorkstation] = useState<Workstation | null>(null);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [showClusters, setShowClusters] = useState(true);
  const [heatmapIntensity, setHeatmapIntensity] = useState(0.8);
  const [L, setL] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load Leaflet on client-side only
  useEffect(() => {
    const initializeLeaflet = async () => {
      try {
        const leaflet = await loadLeaflet();
        if (leaflet) {
          setL(leaflet);
          setIsLoading(false);
        }
      } catch (error) {
        console.error('Failed to load Leaflet:', error);
        setIsLoading(false);
      }
    };

    initializeLeaflet();
  }, []);

  useEffect(() => {
    if (!mapContainerRef.current || !L || isLoading) return;

    // Initialize map
    const map = L.map(mapContainerRef.current, {
      center: [20, 0],
      zoom: 2,
      zoomControl: false,
      attributionControl: false
    });

    // Add tile layer with dark theme support
    const tileLayer = theme.palette.mode === 'dark' 
      ? L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
          attribution: '© OpenStreetMap contributors © CARTO',
          subdomains: 'abcd',
          maxZoom: 19
        })
      : L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '© OpenStreetMap contributors',
          maxZoom: 19
        });

    tileLayer.addTo(map);
    mapRef.current = map;

    // Add custom controls with theme support
    const customControls = (L as any).control({ position: 'topright' });
    customControls.onAdd = () => {
      const div = L.DomUtil.create('div', 'custom-map-controls');
      const isDark = theme.palette.mode === 'dark';
      
      div.style.background = isDark ? '#424242' : 'white';
      div.style.borderRadius = '8px';
      div.style.boxShadow = isDark ? '0 4px 12px rgba(0,0,0,0.4)' : '0 2px 8px rgba(0,0,0,0.15)';
      div.style.padding = '6px';
      div.style.border = isDark ? '1px solid #616161' : '1px solid #e0e0e0';
      
      const buttonStyle = `
        display: block;
        width: 36px;
        height: 36px;
        border: none;
        background: ${isDark ? '#525252' : '#fafafa'};
        color: ${isDark ? '#e0e0e0' : '#424242'};
        cursor: pointer;
        border-radius: 6px;
        margin-bottom: 4px;
        font-size: 16px;
        font-weight: 500;
        transition: all 0.2s ease;
        border: 1px solid ${isDark ? '#616161' : '#e0e0e0'};
      `;
      
      const hoverStyle = `
        background: ${isDark ? '#616161' : '#f0f0f0'} !important;
        transform: scale(1.05);
      `;
      
      div.innerHTML = `
        <button id="zoom-in" style="${buttonStyle}">+</button>
        <button id="zoom-out" style="${buttonStyle}">−</button>
        <button id="center-map" style="${buttonStyle.replace('margin-bottom: 4px;', '')}">⌂</button>
      `;
      
      // Add hover effects
      const buttons = div.querySelectorAll('button');
      buttons.forEach((button: HTMLButtonElement) => {
        button.addEventListener('mouseenter', () => {
          button.style.background = isDark ? '#616161' : '#f0f0f0';
          button.style.transform = 'scale(1.05)';
        });
        button.addEventListener('mouseleave', () => {
          button.style.background = isDark ? '#525252' : '#fafafa';
          button.style.transform = 'scale(1)';
        });
      });
      
      L.DomEvent.disableClickPropagation(div);
      
      div.querySelector('#zoom-in')?.addEventListener('click', () => map.zoomIn());
      div.querySelector('#zoom-out')?.addEventListener('click', () => map.zoomOut());
      div.querySelector('#center-map')?.addEventListener('click', () => {
        map.setView([20, 0], 2);
      });
      
      return div;
    };
    customControls.addTo(map);

    return () => {
      map.remove();
    };
  }, [theme.palette.mode, L, isLoading]);

  useEffect(() => {
    if (!mapRef.current || !L) return;

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    // Add workstation markers
    workstations.forEach(workstation => {
      const marker = L.marker(
        [workstation.coordinates.lat, workstation.coordinates.lng],
        { icon: createCustomIcon(workstation.status, workstation.alertCount, L) }
      );

      // Create popup content
      const popupContent = `
        <div style="
          font-family: 'Roboto', sans-serif;
          min-width: 200px;
          padding: 8px;
        ">
          <div style="
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
            padding-bottom: 8px;
            border-bottom: 1px solid #eee;
          ">
            <div style="
              width: 12px;
              height: 12px;
              background: ${getStatusColor(workstation.status)};
              border-radius: 50%;
            "></div>
            <strong>${workstation.hostname}</strong>
          </div>
          
          <div style="margin-bottom: 8px;">
            <div style="font-size: 12px; color: #666; margin-bottom: 4px;">
              ${workstation.location} • ${workstation.department}
            </div>
            <div style="font-size: 11px; color: #999;">
              ${workstation.ipAddress} • ${workstation.platform}
            </div>
          </div>
          
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 11px;">
            <div>
              <div style="color: #666;">CPU Usage</div>
              <div style="font-weight: 500; color: ${workstation.cpuUsage > 80 ? '#f44336' : workstation.cpuUsage > 60 ? '#ff9800' : '#4caf50'};">
                ${workstation.cpuUsage}%
              </div>
            </div>
            <div>
              <div style="color: #666;">Memory</div>
              <div style="font-weight: 500; color: ${workstation.memoryUsage > 80 ? '#f44336' : workstation.memoryUsage > 60 ? '#ff9800' : '#4caf50'};">
                ${workstation.memoryUsage}%
              </div>
            </div>
            <div>
              <div style="color: #666;">Agents</div>
              <div style="font-weight: 500;">${workstation.agentCount}</div>
            </div>
            <div>
              <div style="color: #666;">Alerts</div>
              <div style="font-weight: 500; color: ${workstation.alertCount > 0 ? '#f44336' : '#4caf50'};">
                ${workstation.alertCount}
              </div>
            </div>
          </div>
          
          ${workstation.alertCount > 0 ? `
            <div style="
              margin-top: 8px;
              padding: 4px 8px;
              background: #ffebee;
              border-left: 3px solid #f44336;
              border-radius: 4px;
              font-size: 11px;
              color: #c62828;
            ">
              ⚠ ${workstation.alertCount} active alert${workstation.alertCount > 1 ? 's' : ''}
            </div>
          ` : ''}
        </div>
      `;

      marker.bindPopup(popupContent, {
        maxWidth: 250,
        className: 'custom-popup'
      });

      marker.on('click', () => {
        setSelectedWorkstation(workstation);
        if (onWorkstationSelect) {
          onWorkstationSelect(workstation);
        }
      });

      marker.addTo(mapRef.current!);
      markersRef.current.push(marker);
    });

    // Update heatmap
    updateHeatmap();
  }, [workstations, onWorkstationSelect, L]);

  // Heatmap effect
  useEffect(() => {
    updateHeatmap();
  }, [showHeatmap, workstations, heatmapIntensity]);

  const updateHeatmap = () => {
    if (!mapRef.current) return;

    // Remove existing heatmap
    if (heatmapLayerRef.current) {
      mapRef.current.removeLayer(heatmapLayerRef.current);
      heatmapLayerRef.current = null;
    }

    if (showHeatmap && workstations.length > 0) {
      // Create heatmap data: [lat, lng, intensity]
      const heatmapData = workstations
        .filter(ws => Math.max(ws.cpuUsage, ws.memoryUsage) >= heatmapIntensity * 100)
        .map(ws => [
          ws.coordinates.lat,
          ws.coordinates.lng,
          Math.max(ws.cpuUsage, ws.memoryUsage) / 100 // Normalize to 0-1
        ]);

      // Create heatmap layer
      heatmapLayerRef.current = (L as any).heatLayer(heatmapData, {
        radius: 30,
        blur: 20,
        maxZoom: 12,
        max: heatmapIntensity,
        gradient: {
          0.0: 'rgba(49, 54, 149, 0.6)',
          0.1: 'rgba(69, 117, 180, 0.7)',
          0.2: 'rgba(116, 173, 209, 0.7)',
          0.3: 'rgba(171, 217, 233, 0.8)',
          0.4: 'rgba(224, 243, 248, 0.8)',
          0.5: 'rgba(255, 255, 204, 0.8)',
          0.6: 'rgba(254, 224, 144, 0.8)',
          0.7: 'rgba(253, 174, 97, 0.9)',
          0.8: 'rgba(244, 109, 67, 0.9)',
          0.9: 'rgba(215, 48, 39, 1.0)',
          1.0: 'rgba(165, 0, 38, 1.0)'
        }
      });

      heatmapLayerRef.current.addTo(mapRef.current);
    }
  };

  const handleZoomIn = () => mapRef.current?.zoomIn();
  const handleZoomOut = () => mapRef.current?.zoomOut();
  const handleCenter = () => mapRef.current?.setView([20, 0], 2);

  const statusCounts = workstations.reduce((acc, ws) => {
    acc[ws.status] = (acc[ws.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // Show loading state while Leaflet is loading
  if (isLoading || !L) {
    return (
      <Card>
        <CardContent>
          <Box
            display="flex"
            alignItems="center"
            justifyContent="center"
            height={500}
            bgcolor={theme.palette.mode === 'dark' ? 'grey.900' : 'grey.100'}
            borderRadius={1}
          >
            <Box textAlign="center">
              <MapOutlined sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                Loading Interactive Map...
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Initializing Leaflet components
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent sx={{ p: 0, position: 'relative' }}>
        {/* Map Controls */}
        <Box
          sx={{
            position: 'absolute',
            top: 16,
            left: 16,
            zIndex: 1000,
            display: 'flex',
            flexDirection: 'column',
            gap: 1
          }}
        >
          <Paper sx={{ p: 1 }}>
            <Stack direction="row" spacing={1} alignItems="center">
              <LocationOnOutlined color="primary" />
              <Typography variant="body2" fontWeight={500}>
                {workstations.length} Workstations
              </Typography>
            </Stack>
          </Paper>
          
          <Paper sx={{ p: 1 }}>
            <Stack spacing={1}>
              <FormControlLabel
                control={
                  <Switch
                    size="small"
                    checked={showClusters}
                    onChange={(e) => setShowClusters(e.target.checked)}
                  />
                }
                label={<Typography variant="caption">Clusters</Typography>}
              />
              <FormControlLabel
                control={
                  <Switch
                    size="small"
                    checked={showHeatmap}
                    onChange={(e) => setShowHeatmap(e.target.checked)}
                  />
                }
                label={
                  <Box display="flex" alignItems="center" gap={0.5}>
                    <SpeedOutlined fontSize="small" />
                    <Typography variant="caption">Performance</Typography>
                  </Box>
                }
              />
            </Stack>
          </Paper>
        </Box>

        {/* Status Legend */}
        <Box
          sx={{
            position: 'absolute',
            bottom: 16,
            left: 16,
            zIndex: 1000
          }}
        >
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              {showHeatmap ? 'Performance Heatmap' : 'Status Legend'}
            </Typography>
            
            {showHeatmap ? (
              <Stack spacing={1.5}>
                <Box display="flex" alignItems="center" gap={1}>
                  <SpeedOutlined fontSize="small" color="primary" />
                  <Typography variant="caption" fontWeight={500}>
                    Performance Intensity
                  </Typography>
                </Box>
                
                <Box>
                  <Box display="flex" justifyContent="space-between" mb={0.5}>
                    <Typography variant="caption" sx={{ fontSize: '10px' }}>
                      Threshold: {Math.round(heatmapIntensity * 100)}%
                    </Typography>
                  </Box>
                  <Slider
                    value={heatmapIntensity}
                    onChange={(_, value) => setHeatmapIntensity(value as number)}
                    min={0}
                    max={1}
                    step={0.05}
                    size="small"
                    sx={{
                      width: 120,
                      height: 4,
                      '& .MuiSlider-track': {
                        background: 'linear-gradient(to right, #313695, #4575b4, #74add1, #abd9e9, #e0f3f8, #ffffcc, #fee090, #fdae61, #f46d43, #d73027, #a50026)',
                        border: 'none'
                      },
                      '& .MuiSlider-rail': {
                        background: 'linear-gradient(to right, #313695, #4575b4, #74add1, #abd9e9, #e0f3f8, #ffffcc, #fee090, #fdae61, #f46d43, #d73027, #a50026)',
                        opacity: 0.3
                      },
                      '& .MuiSlider-thumb': {
                        width: 12,
                        height: 12,
                        backgroundColor: theme.palette.primary.main,
                        border: '2px solid white',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                        '&:hover': {
                          boxShadow: '0 2px 8px rgba(0,0,0,0.3)'
                        }
                      }
                    }}
                  />
                </Box>
                
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Box display="flex" alignItems="center" gap={0.5}>
                    <Box
                      sx={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        bgcolor: '#313695'
                      }}
                    />
                    <Typography variant="caption" sx={{ fontSize: '10px' }}>
                      Low Load
                    </Typography>
                  </Box>
                  <Box display="flex" alignItems="center" gap={0.5}>
                    <Box
                      sx={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        bgcolor: '#a50026'
                      }}
                    />
                    <Typography variant="caption" sx={{ fontSize: '10px' }}>
                      High Load
                    </Typography>
                  </Box>
                </Box>
              </Stack>
            ) : (
              <Stack spacing={1}>
                {Object.entries(statusCounts).map(([status, count]) => (
                  <Box key={status} display="flex" alignItems="center" gap={1}>
                    <Box
                      sx={{
                        width: 12,
                        height: 12,
                        borderRadius: '50%',
                        bgcolor: getStatusColor(status)
                      }}
                    />
                    <Typography variant="caption" sx={{ textTransform: 'capitalize' }}>
                      {status} ({count})
                    </Typography>
                  </Box>
                ))}
              </Stack>
            )}
          </Paper>
        </Box>

        {/* Map Container */}
        <Box
          ref={mapContainerRef}
          sx={{
            height: 500,
            width: '100%',
            borderRadius: 1,
            '& .leaflet-popup-content-wrapper': {
              borderRadius: 1,
              boxShadow: theme.shadows[8]
            },
            '& .custom-popup .leaflet-popup-content': {
              margin: 0,
              padding: 0
            }
          }}
        />

        {/* Selected Workstation Info */}
        {selectedWorkstation && (
          <Box
            sx={{
              position: 'absolute',
              top: 16,
              right: 16,
              zIndex: 1000,
              width: 280
            }}
          >
            <Paper sx={{ p: 2 }}>
              <Box display="flex" alignItems="center" gap={2} mb={2}>
                <Avatar
                  sx={{
                    bgcolor: getStatusColor(selectedWorkstation.status),
                    width: 32,
                    height: 32
                  }}
                >
                  <ComputerOutlined fontSize="small" />
                </Avatar>
                <Box>
                  <Typography variant="subtitle2">
                    {selectedWorkstation.hostname}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {selectedWorkstation.location}
                  </Typography>
                </Box>
                <Chip
                  label={selectedWorkstation.status}
                  size="small"
                  sx={{
                    bgcolor: getStatusColor(selectedWorkstation.status),
                    color: 'white',
                    textTransform: 'capitalize'
                  }}
                />
              </Box>
              
              <Divider sx={{ mb: 2 }} />
              
              <Stack spacing={1}>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="caption">CPU Usage:</Typography>
                  <Typography variant="caption" fontWeight={500}>
                    {selectedWorkstation.cpuUsage}%
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="caption">Memory:</Typography>
                  <Typography variant="caption" fontWeight={500}>
                    {selectedWorkstation.memoryUsage}%
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="caption">Active Agents:</Typography>
                  <Typography variant="caption" fontWeight={500}>
                    {selectedWorkstation.agentCount}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="caption">Alerts:</Typography>
                  <Typography 
                    variant="caption" 
                    fontWeight={500}
                    color={selectedWorkstation.alertCount > 0 ? 'error.main' : 'success.main'}
                  >
                    {selectedWorkstation.alertCount}
                  </Typography>
                </Box>
              </Stack>
            </Paper>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

// Export the component with dynamic loading to prevent SSR issues
const InteractiveWorldMap = dynamic(() => Promise.resolve(InteractiveWorldMapComponent), {
  ssr: false,
  loading: () => (
    <Card>
      <CardContent>
        <Box
          display="flex"
          alignItems="center"
          justifyContent="center"
          height={500}
          bgcolor="grey.100"
          borderRadius={1}
        >
          <Box textAlign="center">
            <MapOutlined sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              Loading Interactive Map...
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  )
});

export default InteractiveWorldMap;
