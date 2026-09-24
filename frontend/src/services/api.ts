// API Service for StockPilot Backend

import axios from 'axios';
import type { SKU, AnalysisResult, SimulationResult } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const inventoryApi = {
  // Get all inventory
  getAll: async (): Promise<SKU[]> => {
    const response = await api.get('/inventory');
    return response.data;
  },

  // Get single SKU
  getById: async (skuId: string): Promise<SKU> => {
    const response = await api.get(`/inventory/${skuId}`);
    return response.data;
  },

  // Get sales history
  getSalesHistory: async (skuId: string, days: number = 30) => {
    const response = await api.get(`/sales-history/${skuId}`, {
      params: { days },
    });
    return response.data;
  },
};

export const analysisApi = {
  // Analyze single SKU
  analyze: async (skuId: string): Promise<AnalysisResult> => {
    const response = await api.post(`/analysis/${skuId}/complete`);
    return response.data;
  },

  // Pattern analysis
  getPattern: async (skuId: string) => {
    const response = await api.post(`/analysis/${skuId}/pattern`);
    return response.data;
  },

  // Forecast
  getForecast: async (skuId: string) => {
    const response = await api.post(`/analysis/${skuId}/forecast`);
    return response.data;
  },

  // Risk assessment
  getRisk: async (skuId: string) => {
    const response = await api.post(`/analysis/${skuId}/risk`);
    return response.data;
  },
};

export const procurementApi = {
  // Analyze SKU for procurement
  analyze: async (skuId: string): Promise<AnalysisResult> => {
    const response = await api.post(`/procurement/analyze/${skuId}`);
    return response.data;
  },

  // Analyze all SKUs
  analyzeAll: async () => {
    const response = await api.post('/procurement/analyze-all');
    return response.data;
  },

  // Get pending approvals
  getPendingApprovals: async () => {
    const response = await api.get('/procurement/pending-approvals');
    return response.data;
  },

  // Auto-generate PO
  autoGenerate: async (skuId: string) => {
    const response = await api.post(`/procurement/auto-generate/${skuId}`, null, {
      params: { created_by: 'frontend_user' },
    });
    return response.data;
  },
};

export const simulationApi = {
  // Run simulation for SKU
  run: async (skuId: string): Promise<SimulationResult> => {
    const response = await api.post(`/simulation/run/${skuId}`);
    return response.data;
  },

  // Get comparison for all SKUs
  getComparison: async () => {
    const response = await api.get('/simulation/comparison');
    return response.data;
  },
};

export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
