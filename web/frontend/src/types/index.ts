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
    version: string;
    status: string;
    message: string;
  };
  python: {
    version: string;
    status: string;
    message: string;
  };
  docker: {
    installed: boolean;
    version: string;
    status: string;
    message: string;
  };
  disk: {
    available_gb: number;
    status: string;
    message: string;
  };
  network: {
    connected: boolean;
    status: string;
    message: string;
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
