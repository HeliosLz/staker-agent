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
  };
  python: {
    name: string;
    status: string;
    supported: boolean;
  };
  docker: {
    name: string;
    status: string;
    supported: boolean;
  };
  disk: {
    name: string;
    status: string;
    supported: boolean;
  };
  network: {
    name: string;
    status: string;
    supported: boolean;
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
