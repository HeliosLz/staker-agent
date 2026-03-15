import { useState, useEffect, useCallback } from 'react';
import { getSocket } from '../services/socket';
import { deployAPI } from '../services/api';

export interface PipelineStep {
  step: number;
  name: string;
  status: 'pending' | 'running' | 'done' | 'failed';
  message: string;
}

export interface PipelineState {
  jobId: string | null;
  steps: PipelineStep[];
  completed: boolean;
  success: boolean;
  error: string | null;
  mnemonic: string | null;
}

const initialState: PipelineState = {
  jobId: null,
  steps: [],
  completed: false,
  success: false,
  error: null,
  mnemonic: null,
};

export interface PipelineConfig {
  network: string;
  client: string;
  fee_recipient?: string;
  withdrawal_address?: string;
  num_validators?: number;
  use_lido_csm?: boolean;
  skip_keys?: boolean;
  keystore_password?: string;
  remote?: { host: string; user?: string; port?: number; ssh_key?: string } | null;
}

export function usePipelineProgress() {
  const [state, setState] = useState<PipelineState>(initialState);

  useEffect(() => {
    const socket = getSocket();

    socket.on('pipeline_progress', (data: {
      job_id: string;
      step: number;
      total: number;
      name: string;
      status: string;
      message: string;
    }) => {
      setState(prev => {
        const stepMap = new Map(prev.steps.map(s => [s.step, s]));
        stepMap.set(data.step, {
          step: data.step,
          name: data.name,
          status: data.status as PipelineStep['status'],
          message: data.message,
        });

        for (let i = 1; i <= data.total; i++) {
          if (!stepMap.has(i)) {
            stepMap.set(i, { step: i, name: `步骤 ${i}`, status: 'pending', message: '' });
          }
        }

        const steps = Array.from(stepMap.values()).sort((a, b) => a.step - b.step);
        return { ...prev, jobId: data.job_id, steps };
      });
    });

    socket.on('pipeline_complete', (data: {
      job_id: string;
      success: boolean;
      mnemonic?: string;
      result?: any;
      error?: string;
    }) => {
      setState(prev => ({
        ...prev,
        jobId: data.job_id,
        completed: true,
        success: data.success,
        error: data.error || null,
        mnemonic: data.mnemonic || null,
      }));
    });

    return () => {
      socket.off('pipeline_progress');
      socket.off('pipeline_complete');
    };
  }, []);

  const startPipeline = useCallback(async (config: PipelineConfig) => {
    setState({ ...initialState, steps: [] });
    try {
      const res = await deployAPI.full(config);
      setState(prev => ({ ...prev, jobId: res.data?.data?.job?.id || null }));
    } catch (err: any) {
      setState(prev => ({
        ...prev,
        completed: true,
        success: false,
        error: err.response?.data?.message || err.message || '请求失败',
      }));
    }
  }, []);

  const reset = useCallback(() => {
    setState(initialState);
  }, []);

  return { ...state, startPipeline, reset };
}
