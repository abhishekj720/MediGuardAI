import { createClient } from '@insforge/sdk';

// Insforge client configuration
// Uses environment variables injected at build time
const INSFORGE_BASE_URL = import.meta.env.VITE_INSFORGE_BASE_URL || 'http://localhost:7130';
const INSFORGE_ANON_KEY = import.meta.env.VITE_INSFORGE_ANON_KEY || '';

export const insforge = createClient({
  baseUrl: INSFORGE_BASE_URL,
  anonKey: INSFORGE_ANON_KEY,
});

export type UserRole = 'doctor' | 'patient';

export type User = {
  id: string;
  email: string;
  emailVerified: boolean;
  profile?: {
    name?: string;
    avatar_url?: string;
    role?: UserRole;
  };
  createdAt: string;
  updatedAt: string;
};
