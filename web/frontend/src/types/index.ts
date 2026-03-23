export interface Network {
  id: string;
  name: string;
  description: string;
  recommended: boolean;
}

export interface Client {
  id: string;
  name: string;
  language: string;
  description: string;
  recommended: boolean;
}

export interface EnvCheck {
  os: {
    name: string;
    status: string;
    supported: boolean;
    error?: string;
  };
  python: {
    name: string;
    status: string;
    supported: boolean;
    error?: string;
  };
  docker: {
    name: string;
    status: string;
    supported: boolean;
    error?: string;
  };
  disk: {
    name: string;
    status: string;
    supported: boolean;
    error?: string;
  };
  network: {
    name: string;
    status: string;
    supported: boolean;
    error?: string;
  };
}

export interface NodeStatus {
  running: boolean;
  network?: string;
  client?: string;
  containers?: Array<{
    name: string;
    status: string;
    uptime?: string;
  }>;
}

export interface ToolCallInfo {
  tool_name: string;
  tool_id: string;
  tool_input: Record<string, unknown>;
  status: 'running' | 'done' | 'failed';
  result?: Record<string, unknown>;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: ToolCallInfo[];
}

// Phase 2: Health monitoring types
export type HealthLevel = 'healthy' | 'degraded' | 'critical';

export interface HealthCheck {
  name: string;
  level: HealthLevel;
  message: string;
  value?: unknown;
  details?: Record<string, unknown>;
  auto_fixable?: boolean;
  timestamp: number;
}

export interface HealthReport {
  overall: HealthLevel;
  checks: HealthCheck[];
  timestamp: number;
}

export interface HealthAlert {
  message: string;
  timestamp?: number;
}