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