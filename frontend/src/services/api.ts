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
  analyze: async (skuId: string) => {
    const response = await api.post(`/procurement/analyze/${skuId}`);
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

// n8n Workflow Integration
const N8N_BASE = import.meta.env.VITE_N8N_URL || 'https://saravanan2007.app.n8n.cloud';

export const n8nApi = {
  // Trigger Workflow 1: PO Approval Flow
  triggerPOApproval: async (skuId: string) => {
    // First create PO via backend
    const poResult = await api.post(`/procurement/auto-generate/${skuId}`, null, {
      params: { created_by: 'n8n_workflow' },
    });

    if (poResult.data.po_created) {
      // Fire-and-forget: trigger n8n workflow (don't await - it has a long-running approval loop)
      const po = poResult.data.purchase_order;
      axios.post(`${N8N_BASE}/webhook/stockpilot-po-approval`, {
        po_id: po.po_id,
        sku_id: po.sku_id,
        product_name: skuId,
        quantity: po.quantity,
        supplier: po.supplier_id,
        cost: po.total_cost,
        reasoning: po.reasoning,
        created_at: po.created_at,
      }).catch(() => {}); // Ignore n8n errors - PO is already in DB
    }

    return poResult.data;
  },

  // Trigger Workflow 2: Critical Alert (fire-and-forget)
  triggerCriticalAlert: async (skuId: string, currentStock: number, riskLevel: string, message: string) => {
    axios.post(`${N8N_BASE}/webhook/stockpilot-critical-alert`, {
      sku_id: skuId,
      current_stock: currentStock,
      risk_level: riskLevel,
      message: message,
    }).catch(() => {});
    return { triggered: true };
  },

  // Trigger Workflow 3: Check all SKUs for reorder
  // Calls backend for results + fires n8n webhook for email/slack alerts
  checkReorder: async () => {
    const response = await api.get('/n8n/check-reorder');

    // Also trigger n8n Workflow 3 if there are alerts
    if (response.data.reorder_needed > 0) {
      try {
        await axios.post(`${N8N_BASE}/webhook/stockpilot-reorder-check`, {
          source: 'frontend_dashboard',
          timestamp: new Date().toISOString(),
        });
      } catch {
        // n8n webhook optional - don't block if it fails
      }
    }

    return response.data;
  },
};

export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
